from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.utils import timezone


def return_400(message, fake_status=None):
    message = {
        'status': fake_status,
        'reason': message,
        'time': int(timezone.now().timestamp())
    }
    raise ValidationError(message)