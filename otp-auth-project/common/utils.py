
import re
import phonenumbers
from rest_framework.response import Response
def success_response(message="Success", data=None, status_code=200):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data or {},
        },
        status=status_code,
    )


def error_response(message="Something went wrong", errors=None, status_code=400):
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors or {},
        },
        status=status_code,
    )

def normalize_mobile_number(country_code: str, mobile: str) -> str:
    # Strip any spaces, dashes, or extra characters the user might have typed.
    cleaned_mobile = re.sub(r"[^\d]", "", mobile)
    cleaned_country_code = country_code.strip()
    if not cleaned_country_code.startswith("+"):
        cleaned_country_code = f"+{cleaned_country_code}"

    full_number = f"{cleaned_country_code}{cleaned_mobile}"

    try:
        parsed = phonenumbers.parse(full_number, None)
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid mobile number.")

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("Invalid mobile number.")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def is_valid_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email or ""))
