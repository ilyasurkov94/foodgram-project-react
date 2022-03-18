import json

from recipes.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    python manage.py CSVexport
    """

    def handle(self, *args, **kwargs):
        Ingredient.objects.all().delete()
        file_path = 'data/ingredients.json'
        with open(file_path, encoding='utf-8') as file:
            data = json.load(file)

            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
