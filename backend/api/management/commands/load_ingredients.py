import csv
from django.core.management.base import BaseCommand
from api.models import Ingredient

class Command(BaseCommand):
    help = 'Load ingredients from CSV file (data/ingredients.csv)'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                name, unit = row
                Ingredient.objects.get_or_create(name=name, measurement_unit=unit)
        self.stdout.write(self.style.SUCCESS('Ingredients loaded!')) 