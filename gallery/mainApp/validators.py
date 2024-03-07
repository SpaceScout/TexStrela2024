from django.core.exceptions import ValidationError


def custom_type_validator(value):
    valid_formats = ['png', 'jpeg', 'jpg', 'dng', 'raw']
    print(value.name.endswith)
    if not any([True if value.name.endswith(i) else False for i in valid_formats]):
        raise ValidationError(f'{value.name} is not a valid image format')