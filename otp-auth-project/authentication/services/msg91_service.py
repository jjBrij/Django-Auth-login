import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MSG91_SEND_OTP_URL = "https://control.msg91.com/api/v5/otp"


class MSG91Service:

    def send_otp(self, mobile_number, otp):

        # MSG91 expects international format.
        # Example: 917461014220
        clean_mobile = mobile_number.replace("+", "").strip()

        params = {
            "template_id": settings.MSG91_TEMPLATE_ID,
            "mobile": clean_mobile,
            "authkey": settings.MSG91_AUTH_KEY,
            "otp": otp,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                MSG91_SEND_OTP_URL,
                params=params,
                headers=headers,
                timeout=15,
            )
            print("MSG91 STATUS:", response.status_code)
            print("MSG91 RESPONSE:", response.text)


            logger.info(
                "MSG91 status=%s response=%s",
                response.status_code,
                response.text,
            )

            response.raise_for_status()

            result = response.json()

            if result.get("type") != "success":
                logger.error("MSG91 rejected OTP request: %s", result)
                return False

            logger.info(
                "MSG91 OTP request successful for %s",
                clean_mobile,
            )

            return True

        except requests.RequestException as exc:
            logger.error(
                "MSG91 request failed for %s: %s",
                clean_mobile,
                exc,
            )
            return False