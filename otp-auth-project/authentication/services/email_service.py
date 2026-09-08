
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class EmailService:
    """Handles sending OTP emails via SMTP."""

    def send_otp(self, email, otp):
       
        subject = f"Your {settings.APP_NAME} verification code"

        context = {
            "app_name": settings.APP_NAME,
            "otp": otp,
            "expiry_minutes": settings.OTP_EXPIRY_SECONDS // 60,
        }
        html_body = render_to_string("emails/otp_email.html", context)
        text_body = (
            f"Your {settings.APP_NAME} verification code is {otp}. "
            f"It expires in {context['expiry_minutes']} minutes. "
            f"Do not share this code with anyone."
        )

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            message.attach_alternative(html_body, "text/html")
            message.send()
            logger.info("OTP email sent successfully to %s", email)
            return True
        except Exception as exc:  # SMTP can raise several different exception types
            logger.error("Failed to send OTP email to %s: %s", email, exc)
            return False
