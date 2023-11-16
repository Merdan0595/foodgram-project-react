import csv
import os
import sys

import django
from foodgram.settings import BASE_DIR
from recipes.models import Ingredient


sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodgram.settings")
django.setup()


path = os.path.join(BASE_DIR, 'data')
os.chdir(path)

with open('ingredients.csv', mode="r", encoding="utf-8") as file:
    reader = csv.reader(file)
    for row in reader:
        name = row[0]
        measurement_unit = row[1] if len(row) > 1 else 'г'

        db = Ingredient(
            name=name,
            measurement_unit=measurement_unit
        )
        db.save()
    print('Данные Ingredient загрузились успешно')
