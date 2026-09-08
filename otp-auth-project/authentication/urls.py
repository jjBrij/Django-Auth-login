from django.urls import path

from . import views


urlpatterns = [

    # Registration
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register"
    ),

    # Email OTP
    path(
        "verify-email-otp/",
        views.VerifyEmailOTPView.as_view(),
        name="verify-email-otp"
    ),

    path(
        "resend-email-otp/",
        views.ResendEmailOTPView.as_view(),
        name="resend-email-otp"
    ),

    # Email login
    path(
        "login/email/",
        views.LoginEmailView.as_view(),
        name="login-email"
    ),

    # Add email to authenticated account
    path(
        "add-email/",
        views.AddEmailView.as_view(),
        name="add-email"
    ),

    # Future mobile OTP
    path(
        "verify-mobile-otp/",
        views.VerifyMobileOTPView.as_view(),
        name="verify-mobile-otp"
    ),

    path(
        "resend-mobile-otp/",
        views.ResendMobileOTPView.as_view(),
        name="resend-mobile-otp"
    ),

    path(
        "login/mobile/",
        views.LoginMobileView.as_view(),
        name="login-mobile"
    ),

    # JWT
    path(
        "token/refresh/",
        views.TokenRefreshView.as_view(),
        name="token-refresh"
    ),

    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout"
    ),

    # Current user
    path(
        "me/",
        views.MeView.as_view(),
        name="me"
    ),
]