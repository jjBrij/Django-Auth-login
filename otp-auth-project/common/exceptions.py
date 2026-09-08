
from rest_framework.views import exception_handler as drf_exception_handler

class APIException(Exception):
    def __init__(self, message, status_code=400, errors=None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}
        super().__init__(message)


def custom_exception_handler(exc, context):
    if isinstance(exc, APIException):
        from rest_framework.response import Response
        return Response(
            {
                "success": False,
                "message": exc.message,
                "errors": exc.errors,
            },
            status=exc.status_code,
        )
    response = drf_exception_handler(exc, context)
    if response is None:
        from rest_framework.response import Response

        return Response(
            {
                "success": False,
                "message": "Something went wrong. Please try again later.",
                "errors": {},
            },
            status=500,
        )
    message = "Request failed"
    errors = response.data

    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = str(response.data["detail"])
            errors = {}
        else:
            first_key = next(iter(response.data), None)
            if first_key:
                first_value = response.data[first_key]
                if isinstance(first_value, list) and first_value:
                    message = str(first_value[0])
                else:
                    message = str(first_value)

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
