from django.core.exceptions import ValidationError


def validate_ingredients_exitsts(value):
    if value is None:
        raise ValidationError('Укажите хотя бы один ингредиент')
