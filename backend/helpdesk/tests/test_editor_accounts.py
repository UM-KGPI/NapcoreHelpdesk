"""Editor accounts: GitHub sign-in, roles read per request, reader-only anonymous tokens, user admin."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import yaml
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from helpdesk.models import EditorAccount
from helpdesk.services import editor_accounts
from helpdesk.tests import test_api

GITHUB = {"GITHUB_OAUTH_CLIENT_ID": "cid", "GITHUB_OAUTH_CLIENT_SECRET": "secret",
          "GITHUB_OAUTH_CALLBACK_URL": "https://helpdesk.test/api/v1/auth/github/callback",
          "EDITOR_APP_URL": "https://helpdesk.test/editor"}


def _fragment(response) -> dict:
    return {key: values[0] for key, values in parse_qs(urlparse(response["Location"]).fragment).items()}


class EditorAccountTestCase(APITestCase):
    _normalized_openapi = test_api.HelpdeskApiTests._normalized_openapi
    assert_matches_schema = test_api.HelpdeskApiTests.assert_matches_schema

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(Path(__file__).resolve().parents[3] / "api" / "openapi.yaml", encoding="utf-8") as handle:
            cls.openapi = yaml.safe_load(handle)

    def bearer(self, token: str) -> dict:
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def anonymous_token(self) -> str:
        return self.client.post(reverse("auth-dev-token"), {}, format="json").json()["token"]

    def account(self, login="alice", roles=("editor",), github_id=101, **fields) -> EditorAccount:
        return EditorAccount.objects.create(github_login=login, github_id=github_id, roles=list(roles), **fields)

    def account_headers(self, account: EditorAccount) -> dict:
        return self.bearer(editor_accounts.account_token(account)[0])


class AnonymousReaderTests(EditorAccountTestCase):
    @override_settings(DEV_JWT_DEFAULT_ROLES=["editor", "reviewer", "publisher"], GITHUB_OAUTH_CLIENT_ID="", GITHUB_OAUTH_CLIENT_SECRET="")
    def test_without_github_sign_in_the_anonymous_token_keeps_its_configured_roles(self):
        response = self.client.post(reverse("auth-dev-token"), {}, format="json")
        self.assertEqual(response.json()["roles"], ["editor", "reviewer", "publisher"])
        self.assertFalse(self.client.get(reverse("auth-config")).json()["githubSignIn"])

    @override_settings(**GITHUB, DEV_JWT_DEFAULT_ROLES=["editor", "reviewer", "publisher"])
    def test_with_github_sign_in_the_anonymous_token_is_a_reader(self):
        self.assertEqual(self.client.post(reverse("auth-dev-token"), {}, format="json").json()["roles"], ["reader"])
        self.assertTrue(self.client.get(reverse("auth-config")).json()["githubSignIn"])
        me = self.client.get(reverse("auth-me"), **self.bearer(self.anonymous_token())).json()
        self.assert_matches_schema("AuthMe", me)
        self.assertEqual((me["kind"], me["roles"], me["account"]), ("anonymous", ["reader"], None))

    @override_settings(**GITHUB)
    def test_a_reader_cannot_reach_editorial_endpoints_but_can_ask(self):
        reader = self.bearer(self.anonymous_token())
        for method, name, kwargs in (
            ("get", "questions-events", {}),
            ("delete", "question-event-detail", {"question_event_id": "1"}),
            ("get", "promotion-candidates", {}),
            ("get", "editorial-semantic-clusters", {}),
            ("get", "editorial-queue", {}),
            ("post", "editorial-queue", {}),
            ("get", "editorial-queue-metrics", {}),
            ("post", "admin-index", {}),
            ("get", "auth-users", {}),
        ):
            with self.subTest(endpoint=name, method=method):
                response = getattr(self.client, method)(reverse(name, kwargs=kwargs), {}, format="json", **reader)
                self.assertEqual(response.status_code, 403)
        # Public pages: trending questions and a question's detail page stay open to readers.
        self.assertEqual(self.client.get(reverse("trending-questions"), **reader).status_code, 200)

    @override_settings(**GITHUB)
    def test_an_editor_account_reaches_the_editorial_endpoints(self):
        headers = self.account_headers(self.account())
        self.assertEqual(self.client.get(reverse("editorial-queue-metrics"), **headers).status_code, 200)
        self.assertEqual(self.client.get(reverse("questions-events"), **headers).status_code, 200)


@override_settings(**GITHUB)
class GitHubSignInTests(EditorAccountTestCase):
    def _start(self):
        response = self.client.get(reverse("auth-github-login"))
        self.assertEqual(response.status_code, 302)
        return parse_qs(urlparse(response["Location"]).query)["state"][0]

    def _callback(self, user: dict, state: str | None = None):
        state = state if state is not None else self._start()
        with patch.object(editor_accounts, "exchange_code", return_value="gh-token") as exchange, patch.object(
            editor_accounts, "fetch_github_user", return_value=user
        ):
            response = self.client.get(reverse("auth-github-callback"), {"code": "c1", "state": state})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://helpdesk.test/editor#"))
        return response, exchange

    def test_login_redirects_to_github_with_a_state_bound_to_a_cookie(self):
        response = self.client.get(reverse("auth-github-login"))
        url = urlparse(response["Location"])
        query = parse_qs(url.query)
        self.assertEqual((url.netloc, url.path), ("github.com", "/login/oauth/authorize"))
        self.assertEqual((query["client_id"], query["scope"]), (["cid"], ["read:user"]))
        self.assertEqual(query["redirect_uri"], [GITHUB["GITHUB_OAUTH_CALLBACK_URL"]])
        cookie = response.cookies[editor_accounts.STATE_COOKIE]
        self.assertTrue(cookie["httponly"] and cookie["secure"])
        self.assertTrue(editor_accounts.state_matches(query["state"][0], cookie.value))

    @override_settings(GITHUB_OAUTH_CLIENT_ID="", GITHUB_OAUTH_CLIENT_SECRET="")
    def test_login_is_unavailable_until_configured(self):
        self.assertEqual(self.client.get(reverse("auth-github-login")).status_code, 404)

    def test_an_invited_login_signs_in_and_is_bound_to_the_github_id(self):
        invited = EditorAccount.objects.create(github_login="alice", roles=["editor", "reviewer"], invited_by="bob")
        response, exchange = self._callback({"id": 101, "login": "Alice", "name": "Alice A.", "avatar_url": "https://a.test/a.png"})
        exchange.assert_called_once_with("c1")
        token = _fragment(response)["token"]
        invited.refresh_from_db()
        self.assertEqual((invited.github_id, invited.name), (101, "Alice A."))
        self.assertIsNotNone(invited.last_login_at)
        me = self.client.get(reverse("auth-me"), **self.bearer(token)).json()
        self.assert_matches_schema("AuthMe", me)
        self.assertEqual((me["kind"], me["roles"], me["account"]["githubLogin"]), ("account", ["editor", "reviewer"], "alice"))

    def test_a_github_user_without_an_account_is_refused(self):
        response, _ = self._callback({"id": 7, "login": "mallory"})
        self.assertEqual(_fragment(response)["authError"], "NOT_INVITED")
        self.assertFalse(EditorAccount.objects.exists())

    @override_settings(EDITOR_ADMIN_GITHUB_LOGINS={"atibaut"})
    def test_a_bootstrap_admin_gets_an_admin_account_on_first_sign_in(self):
        response, _ = self._callback({"id": 55, "login": "ATibaut"})
        self.assertIn("token", _fragment(response))
        self.assertEqual(EditorAccount.objects.get(github_id=55).roles, ["admin"])

    def test_a_disabled_account_is_refused(self):
        self.account(login="alice", github_id=101, is_active=False)
        response, _ = self._callback({"id": 101, "login": "alice"})
        self.assertEqual(_fragment(response)["authError"], "ACCOUNT_DISABLED")

    def test_a_callback_without_the_browser_cookie_is_refused(self):
        state = self._start()
        self.client.cookies.clear()
        response, exchange = self._callback({"id": 101, "login": "alice"}, state=state)
        self.assertEqual(_fragment(response)["authError"], "STATE_MISMATCH")
        exchange.assert_not_called()

    def test_roles_and_disabling_take_effect_at_the_next_request(self):
        account = self.account(roles=["editor"])
        headers = self.account_headers(account)
        account.roles = ["reviewer", "publisher"]
        account.save()
        self.assertEqual(self.client.get(reverse("auth-me"), **headers).json()["roles"], ["publisher", "reviewer"])
        account.is_active = False
        account.save()
        self.assertEqual(self.client.get(reverse("auth-me"), **headers).status_code, 401)


@override_settings(**GITHUB)
class UserAdminTests(EditorAccountTestCase):
    def setUp(self):
        self.admin = self.account(login="root", github_id=1, roles=["admin"])
        self.headers = self.account_headers(self.admin)

    def test_only_admins_manage_users(self):
        editor = self.account_headers(self.account(login="ed", github_id=2, roles=["editor", "publisher"]))
        self.assertEqual(self.client.get(reverse("auth-users"), **editor).status_code, 403)
        self.assertEqual(self.client.get(reverse("auth-users"), **self.headers).status_code, 200)

    def test_invite_change_roles_disable_and_delete(self):
        response = self.client.post(reverse("auth-users"), {"githubLogin": "@Carol", "roles": ["reviewer", "editor"]}, format="json", **self.headers)
        self.assertEqual(response.status_code, 201)
        self.assert_matches_schema("EditorUserResponse", response.json())
        user = response.json()["user"]
        self.assertEqual((user["githubLogin"], user["roles"], user["signedInOnce"], user["invitedBy"]), ("carol", ["editor", "reviewer"], False, "root"))

        again = self.client.post(reverse("auth-users"), {"githubLogin": "carol", "roles": ["editor"]}, format="json", **self.headers)
        self.assertEqual(again.status_code, 409)
        bad = self.client.post(reverse("auth-users"), {"githubLogin": "dave", "roles": ["owner"]}, format="json", **self.headers)
        self.assertEqual(bad.json()["error"]["code"], "INVALID_ROLES")

        detail = reverse("auth-user-detail", kwargs={"account_id": user["id"]})
        changed = self.client.patch(detail, {"roles": ["publisher"], "isActive": False}, format="json", **self.headers).json()["user"]
        self.assertEqual((changed["roles"], changed["isActive"]), (["publisher"], False))
        self.assertEqual(self.client.delete(detail, **self.headers).status_code, 204)
        self.assertFalse(EditorAccount.objects.filter(github_login="carol").exists())

    def test_the_last_active_admin_cannot_be_removed(self):
        detail = reverse("auth-user-detail", kwargs={"account_id": self.admin.pk})
        for payload in ({"roles": ["editor"]}, {"isActive": False}):
            with self.subTest(payload=payload):
                response = self.client.patch(detail, payload, format="json", **self.headers)
                self.assertEqual(response.json()["error"]["code"], "LAST_ADMIN")
        self.assertEqual(self.client.delete(detail, **self.headers).status_code, 409)

        self.account(login="second", github_id=3, roles=["admin"])
        self.assertEqual(self.client.patch(detail, {"roles": ["editor"]}, format="json", **self.headers).status_code, 200)
