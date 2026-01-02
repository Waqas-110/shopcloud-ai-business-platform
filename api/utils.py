from django.http import JsonResponse
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
import json

class APIResponse:
    @staticmethod
    def success(data=None, message="Success", status=200):
        response_data = {
            'success': True,
            'message': message,
            'data': data
        }
        return JsonResponse(response_data, status=status)
    
    @staticmethod
    def error(message="Error occurred", errors=None, status=400):
        response_data = {
            'success': False,
            'message': message,
            'errors': errors or []
        }
        return JsonResponse(response_data, status=status)

class APIValidator:
    @staticmethod
    def validate_decimal(value, field_name, min_value=None):
        try:
            decimal_value = Decimal(str(value))
            if min_value is not None and decimal_value < min_value:
                raise ValidationError(f"{field_name} must be at least {min_value}")
            return decimal_value
        except (ValueError, InvalidOperation):
            raise ValidationError(f"Invalid {field_name} format")
    
    @staticmethod
    def validate_integer(value, field_name, min_value=None):
        try:
            int_value = int(value)
            if min_value is not None and int_value < min_value:
                raise ValidationError(f"{field_name} must be at least {min_value}")
            return int_value
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid {field_name} format")
    
    @staticmethod
    def validate_required(value, field_name):
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")
        return value.strip() if isinstance(value, str) else value

def handle_api_errors(func):
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except ValidationError as e:
            return APIResponse.error(str(e), status=400)
        except json.JSONDecodeError:
            return APIResponse.error("Invalid JSON data", status=400)
        except Exception as e:
            return APIResponse.error(f"Internal server error: {str(e)}", status=500)
    return wrapper