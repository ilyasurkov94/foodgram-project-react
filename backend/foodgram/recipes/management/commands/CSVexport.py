from django.core.management.base import BaseCommand
import csv
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    python manage.py CSVexport --path ../../data/ingredients.csv
    """
    help = 'Creating model objects according the file path specified'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="file path")

    def handle(self, *args, **kwargs):
        model_name = Ingredient
        model_name.objects.all().delete()
        file_path = kwargs['path']
        with open(file_path, "rt", encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',', quotechar='|')
            header = next(reader)
            for row in reader:
                _object_dict = {key: value for key, value in zip(header, row)}
                model_name.objects.create(**_object_dict)
