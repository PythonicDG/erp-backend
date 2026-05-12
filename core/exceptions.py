from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps all DRF errors
    in the standard API response format.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'success': False,
            'message': _get_error_message(response),
        }

        # Include field-level errors for validation failures
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_data['errors'] = response.data

        response.data = custom_data

    return response


def _get_error_message(response):
    """Extract a human-readable error message from the response data."""
    data = response.data

    if isinstance(data, dict):
        # Check common DRF error keys
        if 'detail' in data:
            return str(data['detail'])
        if 'non_field_errors' in data:
            errors = data['non_field_errors']
            return str(errors[0]) if isinstance(errors, list) else str(errors)
        # Return first field error
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f'{key}: {value[0]}'
            return f'{key}: {value}'

    if isinstance(data, list) and data:
        return str(data[0])

    return 'An error occurred'
