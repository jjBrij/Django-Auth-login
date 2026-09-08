from rest_framework import serializers
from common.utils import normalize_mobile_number
from .models import User


class RegisterSerializer(serializers.Serializer):
    """
    POST /api/auth/register/

    Registration requires:
    - name
    - email
    - mobile number
    """

    name = serializers.CharField(
        max_length=150,
        min_length=2
    )

    email = serializers.EmailField(
        max_length=255
    )

    country_code = serializers.CharField(
        max_length=5,
        default="+91"
    )

    mobile = serializers.CharField(
        max_length=15
    )

    def validate(self, data):
        try:
            normalized = normalize_mobile_number(
                data["country_code"],
                data["mobile"]
            )
        except ValueError as exc:
            raise serializers.ValidationError({
                "mobile": str(exc)
            })

        data["normalized_mobile"] = normalized

        # Normalize email so login/registration behave consistently
        data["email"] = data["email"].strip().lower()

        return data


class VerifyEmailOTPSerializer(serializers.Serializer):
    """
    POST /api/auth/verify-email-otp/
    """

    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=4,
        max_length=4
    )

    def validate(self, data):
        data["email"] = data["email"].strip().lower()
        return data


class ResendEmailOTPSerializer(serializers.Serializer):
    """
    POST /api/auth/resend-email-otp/
    """

    email = serializers.EmailField()

    def validate(self, data):
        data["email"] = data["email"].strip().lower()
        return data


class LoginEmailSerializer(serializers.Serializer):
    """
    POST /api/auth/login/email/
    """

    email = serializers.EmailField()

    def validate(self, data):
        data["email"] = data["email"].strip().lower()
        return data


class AddEmailSerializer(serializers.Serializer):
    """
    POST /api/auth/add-email/

    Used when an existing authenticated user wants
    to add/change their email address.
    """

    email = serializers.EmailField()

    def validate(self, data):
        data["email"] = data["email"].strip().lower()
        return data


# ---------------------------------------------------------
# MOBILE OTP SERIALIZERS
# Keep these for future mobile OTP authentication.
# ---------------------------------------------------------

class VerifyMobileOTPSerializer(serializers.Serializer):
    """
    POST /api/auth/verify-mobile-otp/
    """

    mobile = serializers.CharField(max_length=15)

    country_code = serializers.CharField(
        max_length=5,
        default="+91"
    )

    otp = serializers.CharField(
        min_length=4,
        max_length=4
    )

    def validate(self, data):
        try:
            normalized = normalize_mobile_number(
                data["country_code"],
                data["mobile"]
            )
        except ValueError as exc:
            raise serializers.ValidationError({
                "mobile": str(exc)
            })

        data["normalized_mobile"] = normalized
        return data


class ResendMobileOTPSerializer(serializers.Serializer):
    """
    POST /api/auth/resend-mobile-otp/
    """

    mobile = serializers.CharField(max_length=15)

    country_code = serializers.CharField(
        max_length=5,
        default="+91"
    )

    def validate(self, data):
        try:
            normalized = normalize_mobile_number(
                data["country_code"],
                data["mobile"]
            )
        except ValueError as exc:
            raise serializers.ValidationError({
                "mobile": str(exc)
            })

        data["normalized_mobile"] = normalized
        return data


class LoginMobileSerializer(serializers.Serializer):
    """
    POST /api/auth/login/mobile/

    Keep this for future mobile OTP login.
    """

    mobile = serializers.CharField(max_length=15)

    country_code = serializers.CharField(
        max_length=5,
        default="+91"
    )

    def validate(self, data):
        try:
            normalized = normalize_mobile_number(
                data["country_code"],
                data["mobile"]
            )
        except ValueError as exc:
            raise serializers.ValidationError({
                "mobile": str(exc)
            })

        data["normalized_mobile"] = normalized
        return data


class TokenRefreshRequestSerializer(serializers.Serializer):
    """
    POST /api/auth/token/refresh/
    """

    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """
    POST /api/auth/logout/
    """

    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """
    GET /api/auth/me/
    """

    class Meta:
        model = User

        fields = [
            "id",
            "name",
            "email",
            "mobile_number",
            "country_code",
            "is_mobile_verified",
            "is_email_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields