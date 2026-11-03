"""
Editor accounts: sign-in with GitHub, roles per person, and the tokens the API accepts.

Anonymous visitors keep the auto-issued token (DevTokenView). Once GitHub sign-in is configured
that token carries only the "reader" role: asking questions and giving feedback. Editorial work
(queue, review, FAQ, harvest and index) needs an EditorAccount, which an admin creates by inviting
a GitHub login with roles. The first sign-in binds the account to the GitHub user id.

The OAuth state is signed and bound to the browser by a cookie holding the same nonce, so a
callback cannot be replayed in another browser. Tokens of accounts name the GitHub user id
("github:<id>"); authentication reads the account's current roles and active flag on every
request, so a role change or a disabled account takes effect at once.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-03  |  Modified: 2026-11-03
"""

from __future__ import annotations

import datetime as dt
import json
import secrets
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
import jwt
from django.conf import settings
from django.core import signing
from django.utils import timezone

from helpdesk.models import EditorAccount

READER_ROLE = "reader"
GITHUB_SUBJECT_PREFIX = "github:"
STATE_COOKIE = "napcore_github_state"
STATE_MAX_AGE_SECONDS = 600
_STATE_SALT = "helpdesk.github-oauth"
_GITHUB_TIMEOUT_SECONDS = 10


class SignInRefused(Exception):
    """GitHub confirmed who the person is, but they may not enter the editor."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def github_sign_in_configured() -> bool:
    return bool(settings.GITHUB_OAUTH_CLIENT_ID and settings.GITHUB_OAUTH_CLIENT_SECRET)


def anonymous_roles() -> list[str]:
    """Roles of the auto-issued token: reader only once accounts exist to do editorial work."""

    return [READER_ROLE] if github_sign_in_configured() else list(settings.DEV_JWT_DEFAULT_ROLES)


def normalise_login(login: str) -> str:
    return (login or "").strip().lstrip("@").lower()


def clean_roles(roles) -> list[str]:
    """The known editor roles among `roles`, in a fixed order; raises ValueError for an unknown one."""

    wanted = {str(role).strip().lower() for role in (roles or []) if str(role).strip()}
    unknown = wanted - set(EditorAccount.ROLES)
    if unknown:
        raise ValueError(f"Unknown roles: {', '.join(sorted(unknown))}")
    return [role for role in EditorAccount.ROLES if role in wanted]


def issue_token(subject: str, roles: list[str], ttl_minutes: int, **claims) -> tuple[str, int]:
    """A signed API token and its lifetime in seconds."""

    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": subject,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=ttl_minutes)).timestamp()),
        **claims,
    }
    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM), ttl_minutes * 60


def account_token(account: EditorAccount) -> tuple[str, int]:
    return issue_token(
        f"{GITHUB_SUBJECT_PREFIX}{account.github_id}",
        list(account.roles),
        settings.EDITOR_JWT_TTL_MINUTES,
        login=account.github_login,
        name=account.name,
    )


def account_for_subject(subject: str) -> EditorAccount | None:
    """The account a token names, or None for a token that names no account (anonymous, tests)."""

    if not subject.startswith(GITHUB_SUBJECT_PREFIX):
        return None
    github_id = subject[len(GITHUB_SUBJECT_PREFIX):]
    if not github_id.isdigit():
        return None
    return EditorAccount.objects.filter(github_id=int(github_id)).first()


# --- OAuth flow -------------------------------------------------------------------------------


def new_state() -> tuple[str, str]:
    """A signed state for the authorize URL and the nonce to keep in the browser's cookie."""

    nonce = secrets.token_urlsafe(24)
    return signing.dumps({"nonce": nonce}, salt=_STATE_SALT), nonce


def state_matches(state: str, cookie_nonce: str) -> bool:
    try:
        payload = signing.loads(state or "", salt=_STATE_SALT, max_age=STATE_MAX_AGE_SECONDS)
    except signing.BadSignature:  # includes SignatureExpired
        return False
    return bool(cookie_nonce) and secrets.compare_digest(str(payload.get("nonce", "")), cookie_nonce)


def authorize_url(state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GITHUB_OAUTH_CALLBACK_URL,
            "scope": "read:user",
            "state": state,
            "allow_signup": "false",
        }
    )
    return f"https://github.com/login/oauth/authorize?{query}"


def _ssl_context() -> ssl.SSLContext:
    if not settings.GITHUB_API_VERIFY_SSL:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    return ssl.create_default_context(cafile=settings.GITHUB_CA_BUNDLE or certifi.where())


def _github_json(request: Request) -> dict:
    with urlopen(request, timeout=_GITHUB_TIMEOUT_SECONDS, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_code(code: str) -> str:
    """The GitHub access token for an authorization code; ValueError when GitHub refuses it."""

    body = urlencode(
        {
            "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
            "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_OAUTH_CALLBACK_URL,
        }
    ).encode("utf-8")
    request = Request(
        "https://github.com/login/oauth/access_token",
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    payload = _github_json(request)
    access_token = payload.get("access_token")
    if not access_token:
        raise ValueError(payload.get("error_description") or payload.get("error") or "no access token")
    return str(access_token)


def fetch_github_user(access_token: str) -> dict:
    request = Request(
        "https://api.github.com/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    user = _github_json(request)
    if not user.get("id") or not user.get("login"):
        raise ValueError("GitHub returned no user")
    return user


def sign_in_github_user(user: dict) -> EditorAccount:
    """The account of a GitHub user GitHub has just confirmed; SignInRefused if they have none."""

    github_id = int(user["id"])
    login = normalise_login(user["login"])
    account = EditorAccount.objects.filter(github_id=github_id).first()
    if account is None:
        # An invitation names a login only; the first sign-in binds it to the GitHub user id.
        account = EditorAccount.objects.filter(github_login=login, github_id__isnull=True).first()
    if account is None and login in settings.EDITOR_ADMIN_GITHUB_LOGINS:
        account = EditorAccount(github_login=login, roles=[EditorAccount.ROLE_ADMIN], invited_by="EDITOR_ADMIN_GITHUB_LOGINS")
    if account is None:
        raise SignInRefused("NOT_INVITED", f"GitHub user {login} has no editor account. Ask an admin to invite you.")
    if not account.is_active:
        raise SignInRefused("ACCOUNT_DISABLED", f"The editor account of {login} is disabled.")
    if not account.roles:
        raise SignInRefused("NO_ROLES", f"The editor account of {login} has no roles yet.")

    # Keep the stored login current: the account follows the GitHub id through a rename.
    if account.github_login != login and not EditorAccount.objects.filter(github_login=login).exclude(pk=account.pk).exists():
        account.github_login = login
    account.github_id = github_id
    account.name = str(user.get("name") or "")[:255]
    account.avatar_url = str(user.get("avatar_url") or "")[:200]
    account.last_login_at = timezone.now()
    account.save()
    return account


def active_admin_count(exclude: EditorAccount | None = None) -> int:
    accounts = EditorAccount.objects.filter(is_active=True, roles__contains=[EditorAccount.ROLE_ADMIN])
    if exclude is not None:
        accounts = accounts.exclude(pk=exclude.pk)
    return accounts.count()
