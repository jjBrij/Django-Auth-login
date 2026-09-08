"""
JWTService - small helper for creating access/refresh tokens for a user.

We use the well-known `djangorestframework-simplejwt` package instead of
writing our own JWT code. This file just wraps its `RefreshToken` class
so views don't need to import simplejwt directly - keeps views.py focused
on request/response handling only.
"""

from rest_framework_simplejwt.tokens import RefreshToken


class JWTService:
    def generate_tokens_for_user(self, user):
        """
        Given a User instance, returns a dict with fresh access and
        refresh tokens:
            {"access": "...", "refresh": "..."}

        - access token: short-lived (see SIMPLE_JWT settings), sent with
          every authenticated API request.
        - refresh token: longer-lived, used only to obtain a new access
          token via POST /api/auth/token/refresh/.
        """
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
