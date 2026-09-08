
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from common.exceptions import APIException
from common.utils import success_response
from .models import User
from .serializers import (
    AddEmailSerializer,
    LoginEmailSerializer,
    LoginMobileSerializer,
    LogoutSerializer,
    RegisterSerializer,
    ResendEmailOTPSerializer,
    ResendMobileOTPSerializer,
    TokenRefreshRequestSerializer,
    UserSerializer,
    VerifyEmailOTPSerializer,
    VerifyMobileOTPSerializer,
)
from .services.email_service import EmailService
from .services.jwt_service import JWTService
from .services.msg91_service import MSG91Service
from .services.otp_service import OTPService
otp_service = OTPService()
msg91_service = MSG91Service()
email_service = EmailService()
jwt_service = JWTService()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        name = data["name"]
        email = data["email"]
        mobile = data["normalized_mobile"]
        country_code = data["country_code"]

        # Check whether mobile already belongs to a verified account
        existing_user = User.objects.filter(
            mobile_number=mobile
        ).first()

        if existing_user and existing_user.is_mobile_verified:
            raise APIException(
                "This mobile number is already registered. Please log in instead.",
                status_code=409,
            )

        # Check whether email already belongs to another account
        existing_email_user = User.objects.filter(
            email=email
        ).first()

        if existing_email_user:
            if existing_email_user.id != getattr(existing_user, "id", None):
                raise APIException(
                    "This email address is already registered. Please log in instead.",
                    status_code=409,
                )

        # Existing unverified registration
        if existing_user:
            existing_user.name = name
            existing_user.email = email
            existing_user.country_code = country_code
            existing_user.is_email_verified = False

            existing_user.save(
                update_fields=[
                    "name",
                    "email",
                    "country_code",
                    "is_email_verified",
                    "updated_at",
                ]
            )

        # New registration
        else:
            existing_user = User.objects.create_user(
                mobile_number=mobile,
                country_code=country_code,
                name=name,
                email=email,
            )

        # Generate email OTP
        otp = otp_service.generate_and_store(
            "email",
            email
        )

        # Send OTP to email
        email_service.send_otp(
            email,
            otp
        )

        return success_response(
            message="OTP sent successfully to your email.",
            data={
                "next_step": "verify_email_otp"
            },
            status_code=201,
        )
class VerifyMobileOTPView(APIView):
  
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyMobileOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mobile = data["normalized_mobile"]

        user = User.objects.filter(mobile_number=mobile).first()
        if not user:
            raise APIException("No account found for this mobile number.", status_code=404)

        otp_service.verify("mobile", mobile, data["otp"])

        was_already_verified = user.is_mobile_verified
        if not was_already_verified:
            user.is_mobile_verified = True
            user.save(update_fields=["is_mobile_verified", "updated_at"])
            return success_response(message="Mobile number verified successfully")

        # This was a login attempt (mobile was already verified before).
        tokens = jwt_service.generate_tokens_for_user(user)
        return success_response(
            message="Login successful",
            data={"access_token": tokens["access"], "refresh_token": tokens["refresh"]},
        )


class ResendMobileOTPView(APIView):
  
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendMobileOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data["normalized_mobile"]

        if not User.objects.filter(mobile_number=mobile).exists():
            raise APIException("No account found for this mobile number.", status_code=404)

        otp = otp_service.generate_and_store("mobile", mobile)
        msg91_service.send_otp(mobile, otp)

        return success_response(message="OTP resent successfully")
class LoginMobileView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginMobileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data["normalized_mobile"]

        user = User.objects.filter(mobile_number=mobile).first()
        if not user or not user.is_mobile_verified:
            # Same message either way, so we don't reveal WHICH numbers
            # exist in our system (prevents user enumeration).
            raise APIException("No verified account found for this mobile number.", status_code=404)

        otp = otp_service.generate_and_store("mobile", mobile)
        msg91_service.send_otp(mobile, otp)

        return success_response(
            message="OTP sent successfully",
            data={"next_step": "verify_mobile_otp"},
        )
class LoginEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email=email
        ).first()

        if not user:
            raise APIException(
                "No account found for this email address.",
                status_code=404,
            )

        if not user.is_active:
            raise APIException(
                "This account is inactive.",
                status_code=403,
            )

        # Generate email OTP
        otp = otp_service.generate_and_store(
            "email",
            email
        )

        # Send OTP to email
        email_service.send_otp(
            email,
            otp
        )

        return success_response(
            message="OTP sent successfully to your email.",
            data={
                "next_step": "verify_email_otp"
            },
        )
class VerifyEmailOTPView(APIView):
   
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data["email"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise APIException("No account found for this email address.", status_code=404)

        otp_service.verify("email", email, data["otp"])

        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified", "updated_at"])

        tokens = jwt_service.generate_tokens_for_user(user)
        return success_response(
            message="Email verified successfully",
            data={"access_token": tokens["access"], "refresh_token": tokens["refresh"]},
        )


class ResendEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if not User.objects.filter(email=email).exists():
            raise APIException("No account found for this email address.", status_code=404)

        otp = otp_service.generate_and_store("email", email)
        email_service.send_otp(email, otp)

        return success_response(message="OTP resent successfully")


class AddEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            raise APIException("This email address is already in use.", status_code=409)

        request.user.email = email
        request.user.is_email_verified = False
        request.user.save(update_fields=["email", "is_email_verified", "updated_at"])

        otp = otp_service.generate_and_store("email", email)
        email_service.send_otp(email, otp)

        return success_response(
            message="OTP sent to email",
            data={"next_step": "verify_email_otp"},
        )

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            old_refresh = RefreshToken(serializer.validated_data["refresh"])
            user_id = old_refresh["user_id"]
        except TokenError:
            raise APIException("Invalid or expired refresh token.", status_code=401)

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise APIException("Invalid or expired refresh token.", status_code=401)
        new_tokens = jwt_service.generate_tokens_for_user(user)
        old_refresh.blacklist()

        return success_response(
            message="Token refreshed successfully",
            data={"access_token": new_tokens["access"], "refresh_token": new_tokens["refresh"]},
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise APIException("Invalid or already-invalidated refresh token.", status_code=400)

        return success_response(message="Logged out successfully")
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(message="User fetched successfully", data=serializer.data)
