# backend/recipes/management/commands/load_ingredients.py
import json
import os  # Для работы с путями к файлам
from django.core.management.base import BaseCommand
from django.conf import settings  # Для доступа к BASE_DIR
from recipes.models import Ingredient

# Нам нужен файл в foodgram-st/data/ingredients.json
DATA_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')


class Command(BaseCommand):
    help = f'Loads ingredients from {DATA_FILE_PATH}'

    def handle(self, *args, **options):
        if not Ingredient.objects.exists():
            self.stdout.write(self.style.WARNING(
                'База ингредиентов пуста. Загружаем данные...'
            ))
            try:
                with open(DATA_FILE_PATH, 'r', encoding='utf-8') as file:
                    ingredients_data = json.load(file)

                ingredients_to_create = []
                for item in ingredients_data:
                    name = item.get('name')
                    measurement_unit = item.get('measurement_unit')
                    if name and measurement_unit:
                        ingredients_to_create.append(
                            Ingredient(
                                name=name.strip(),
                                measurement_unit=measurement_unit.strip()
                            )
                        )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Пропущен ингредиент с неполными данными: {item}'
                        ))

                # Используем bulk_create для эффективной вставки
                Ingredient.objects.bulk_create(ingredients_to_create)

                self.stdout.write(self.style.SUCCESS(
                    f'Успешно загружено {len(ingredients_to_create)} ингредиентов.'
                ))

            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(
                    f'Файл не найден: {DATA_FILE_PATH}'
                ))
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(
                    f'Ошибка декодирования JSON файла: {DATA_FILE_PATH}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Произошла ошибка при загрузке: {e}'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                'В базе уже есть ингредиенты. Загрузка не требуется.'
            ))
