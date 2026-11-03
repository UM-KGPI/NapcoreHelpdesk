"""
Editor sign-in with GitHub and the admins' user management (services/editor_accounts.py).

The callback returns the browser to the editor with the token in the URL fragment (#token=...),
which is not sent to any server or written to access logs; the editor reads it and removes it.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-03  |  Modified: 2026-11-03
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from helpdesk.models import EditorAccount
from helpdesk.services import editor_accounts
from helpdesk.services.editor_accounts import SignInRefused

from .views import _error_response, _request_id, _request_roles

logger = logging.getLogger(__name__)


def _editor_redirect(**fragment: str) -> HttpResponseRedirect:
    response = HttpResponseRedirect(f"{settings.EDITOR_APP_URL}#{urlencode(fragment)}")
    response.delete_cookie(editor_accounts.STATE_COOKIE, path="/")
    return response


def _account_payload(account: EditorAccount) -> dict:
    return {
        "id": account.pk,
        "githubLogin": account.github_login,
        "name": account.name,
        "avatarUrl": account.avatar_url,
        "roles": list(account.roles),
        "isActive": account.is_active,
        "signedInOnce": account.github_id is not None,
        "invitedBy": account.invited_by,
        "lastLoginAt": account.last_login_at.isoformat() if account.last_login_at else None,
        "createdAt": account.created_at.isoformat(),
    }


def _forbid_unless_admin(request, request_id):
    if "admin" in _request_roles(request):
        return None
    return _error_response(
        code="FORBIDDEN",
        message="Managing users requires the admin role.",
        request_id=request_id,
        http_status=status.HTTP_403_FORBIDDEN,
    )


class AuthConfigView(APIView):
    """Whether the editor offers GitHub sign-in (no token needed)."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"githubSignIn": editor_accounts.github_sign_in_configured()}, status=status.HTTP_200_OK)


class GitHubLoginView(APIView):
    """Start the GitHub sign-in: remember a nonce in a cookie and send the browser to GitHub."""

    permission_classes = [AllowAny]

    def get(self, request):
        if not editor_accounts.github_sign_in_configured():
            return _error_response(
                code="SIGN_IN_DISABLED",
                message="GitHub sign-in is not configured.",
                request_id=_request_id(request),
                http_status=status.HTTP_404_NOT_FOUND,
            )
        state, nonce = editor_accounts.new_state()
        response = HttpResponseRedirect(editor_accounts.authorize_url(state))
        response.set_cookie(
            editor_accounts.STATE_COOKIE,
            nonce,
            max_age=editor_accounts.STATE_MAX_AGE_SECONDS,
            path="/",
            httponly=True,
            secure=settings.GITHUB_OAUTH_CALLBACK_URL.startswith("https://"),
            samesite="Lax",
        )
        return response


class GitHubCallbackView(APIView):
    """GitHub returns here: check the state, identify the user, and hand the editor its token."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        if request.query_params.get("error"):
            return _editor_redirect(authError="GITHUB_DENIED", authMessage=request.query_params.get("error_description", ""))
        if not editor_accounts.state_matches(
            request.query_params.get("state", ""), request.COOKIES.get(editor_accounts.STATE_COOKIE, "")
        ):
            return _editor_redirect(authError="STATE_MISMATCH", authMessage="The sign-in expired or was started elsewhere. Try again.")
        try:
            access_token = editor_accounts.exchange_code(request.query_params.get("code", ""))
            user = editor_accounts.fetch_github_user(access_token)
        except Exception:
            logger.exception("GitHub sign-in failed")
            return _editor_redirect(authError="GITHUB_ERROR", authMessage="GitHub could not confirm the sign-in. Try again.")
        try:
            account = editor_accounts.sign_in_github_user(user)
        except SignInRefused as refused:
            return _editor_redirect(authError=refused.code, authMessage=str(refused))
        token, expires_in = editor_accounts.account_token(account)
        return _editor_redirect(token=token, expiresIn=str(expires_in))


class MeView(APIView):
    """Who the token belongs to: an editor account, or the anonymous reader."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth if isinstance(request.auth, dict) else {}
        subject = str(token.get("sub", ""))
        account = editor_accounts.account_for_subject(subject)
        return Response(
            {
                "subject": subject,
                "kind": "account" if account else "anonymous",
                "roles": sorted(_request_roles(request)),
                "account": _account_payload(account) if account else None,
                "githubSignIn": editor_accounts.github_sign_in_configured(),
            },
            status=status.HTTP_200_OK,
        )


class InviteSerializer(serializers.Serializer):
    githubLogin = serializers.RegexField(r"^@?[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
    roles = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class AccountUpdateSerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.CharField(), required=False)
    isActive = serializers.BooleanField(required=False)


class UsersView(APIView):
    """Admins list the editor accounts and invite a GitHub login with roles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        request_id = _request_id(request)
        forbidden = _forbid_unless_admin(request, request_id)
        if forbidden:
            return forbidden
        accounts = [_account_payload(account) for account in EditorAccount.objects.all()]
        return Response({"requestId": request_id, "users": accounts, "roles": list(EditorAccount.ROLES)}, status=status.HTTP_200_OK)

    def post(self, request):
        request_id = _request_id(request)
        forbidden = _forbid_unless_admin(request, request_id)
        if forbidden:
            return forbidden
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login = editor_accounts.normalise_login(serializer.validated_data["githubLogin"])
        try:
            roles = editor_accounts.clean_roles(serializer.validated_data["roles"])
        except ValueError as exc:
            return _error_response(code="INVALID_ROLES", message=str(exc), request_id=request_id)
        if EditorAccount.objects.filter(github_login=login).exists():
            return _error_response(
                code="ALREADY_INVITED", message=f"{login} already has an editor account.", request_id=request_id,
                http_status=status.HTTP_409_CONFLICT,
            )
        inviter = str((request.auth or {}).get("login") or (request.auth or {}).get("sub") or "")[:39]
        account = EditorAccount.objects.create(github_login=login, roles=roles, invited_by=inviter)
        return Response({"requestId": request_id, "user": _account_payload(account)}, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """Admins change an account's roles, disable or re-enable it, or delete it.

    The last active admin cannot lose the admin role, be disabled or be deleted, so the editor
    always keeps someone who can manage it.
    """

    permission_classes = [IsAuthenticated]

    def _account(self, request, account_id):
        request_id = _request_id(request)
        forbidden = _forbid_unless_admin(request, request_id)
        if forbidden:
            return None, forbidden
        account = EditorAccount.objects.filter(pk=account_id).first()
        if account is None:
            return None, _error_response(
                code="NOT_FOUND", message="No such editor account.", request_id=request_id, http_status=status.HTTP_404_NOT_FOUND
            )
        return account, None

    def _would_remove_last_admin(self, account: EditorAccount, roles: list[str], active: bool) -> bool:
        stays_admin = active and EditorAccount.ROLE_ADMIN in roles
        is_admin = account.is_active and EditorAccount.ROLE_ADMIN in account.roles
        return is_admin and not stays_admin and editor_accounts.active_admin_count(exclude=account) == 0

    def patch(self, request, account_id: int):
        request_id = _request_id(request)
        with transaction.atomic():
            account, error = self._account(request, account_id)
            if error:
                return error
            serializer = AccountUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            try:
                roles = editor_accounts.clean_roles(data["roles"]) if "roles" in data else list(account.roles)
            except ValueError as exc:
                return _error_response(code="INVALID_ROLES", message=str(exc), request_id=request_id)
            active = data.get("isActive", account.is_active)
            if self._would_remove_last_admin(account, roles, active):
                return _error_response(
                    code="LAST_ADMIN", message="This is the last active admin; make another admin first.",
                    request_id=request_id, http_status=status.HTTP_409_CONFLICT,
                )
            account.roles, account.is_active = roles, active
            account.save(update_fields=["roles", "is_active", "updated_at"])
        return Response({"requestId": request_id, "user": _account_payload(account)}, status=status.HTTP_200_OK)

    def delete(self, request, account_id: int):
        request_id = _request_id(request)
        with transaction.atomic():
            account, error = self._account(request, account_id)
            if error:
                return error
            if self._would_remove_last_admin(account, [], False):
                return _error_response(
                    code="LAST_ADMIN", message="This is the last active admin; make another admin first.",
                    request_id=request_id, http_status=status.HTTP_409_CONFLICT,
                )
            account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
