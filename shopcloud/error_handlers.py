"""
Enhanced error handling utilities for ShopCloud
"""
import logging
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError, PermissionDenied
from decimal import InvalidOperation

logger = logging.getLogger(__name__)

def handle_view_errors(redirect_url=None, json_response=False):
    """
    Decorator to handle common view errors with consistent messaging
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except PermissionDenied:
                logger.warning(f"Permission denied for user {request.user.username} in {view_func.__name__}")
                if json_response:
                    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
                messages.error(request, 'You do not have permission to perform this action.')
                return redirect(redirect_url or 'dashboard:main')
            except ValidationError as e:
                logger.warning(f"Validation error in {view_func.__name__}: {str(e)}")
                if json_response:
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                messages.error(request, f'Validation error: {str(e)}')
                return redirect(redirect_url or request.META.get('HTTP_REFERER', 'dashboard:main'))
            except IntegrityError as e:
                logger.error(f"Database integrity error in {view_func.__name__}: {str(e)}")
                if json_response:
                    return JsonResponse({'success': False, 'error': 'Data integrity error'}, status=400)
                messages.error(request, 'A database error occurred. Please check your data and try again.')
                return redirect(redirect_url or request.META.get('HTTP_REFERER', 'dashboard:main'))
            except DatabaseError as e:
                logger.error(f"Database error in {view_func.__name__}: {str(e)}")
                if json_response:
                    return JsonResponse({'success': False, 'error': 'Database error'}, status=500)
                messages.error(request, 'A database error occurred. Please try again later.')
                return redirect(redirect_url or 'dashboard:main')
            except Exception as e:
                logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", exc_info=True)
                if json_response:
                    return JsonResponse({'success': False, 'error': 'An unexpected error occurred'}, status=500)
                messages.error(request, 'An unexpected error occurred. Please try again.')
                return redirect(redirect_url or 'dashboard:main')
        return wrapper
    return decorator

def validate_decimal_field(value, field_name, min_value=0, allow_zero=True):
    """Validate decimal fields with proper error messages"""
    try:
        decimal_value = float(value) if isinstance(value, str) else value
        if decimal_value < min_value:
            raise ValidationError(f'{field_name} cannot be less than {min_value}')
        if not allow_zero and decimal_value == 0:
            raise ValidationError(f'{field_name} must be greater than zero')
        return decimal_value
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError(f'Invalid {field_name} format')

def validate_integer_field(value, field_name, min_value=0):
    """Validate integer fields with proper error messages"""
    try:
        int_value = int(value)
        if int_value < min_value:
            raise ValidationError(f'{field_name} cannot be less than {min_value}')
        return int_value
    except (ValueError, TypeError):
        raise ValidationError(f'Invalid {field_name} format')

def validate_required_field(value, field_name):
    """Validate required fields"""
    if not value or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f'{field_name} is required')
    return value.strip() if isinstance(value, str) else value

def log_user_action(user, action, details=None):
    """Log user actions for audit trail"""
    logger.info(f"User {user.username} performed action: {action}" + 
                (f" - {details}" if details else ""))