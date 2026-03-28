from __future__ import annotations

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions


class JWTBearerAuthentication(authentication.BaseAuthentication):
    """Bearer JWT authentication using shared-secret validation."""

    keyword = "bearer"

    def authenticate(self, request):
        # DRF passes raw bytes for Authorization; decode once and parse consistently.
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid bearer authorization header format.")

        raw_token = parts[1].strip()

        # Build decode options dynamically so issuer/audience checks are optional but strict when set.
        decode_kwargs = {
            "key": settings.JWT_SECRET_KEY,
            "algorithms": [settings.JWT_ALGORITHM],
        }
        if settings.JWT_AUDIENCE:
            decode_kwargs["audience"] = settings.JWT_AUDIENCE
        else:
            decode_kwargs["options"] = {"verify_aud": False}
        if settings.JWT_ISSUER:
            decode_kwargs["issuer"] = settings.JWT_ISSUER

        try:
            payload = jwt.decode(raw_token, **decode_kwargs)
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed("JWT has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid JWT bearer token.") from exc

        subject = str(payload.get("sub") or "").strip()
        if not subject:
            raise exceptions.AuthenticationFailed("JWT subject claim 'sub' is required.")

        # Use deterministic local usernames for principal mapping and permission checks.
        username = f"jwt-{subject}"[:150]

        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(username=username)
        if not user.has_usable_password():
            return user, payload

        user.set_unusable_password()
        user.save(update_fields=["password"])
        return user, payload

    def authenticate_header(self, request):
        return "Bearer"
