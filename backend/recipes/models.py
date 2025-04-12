# backend/recipes/models.py
from django.db import models
from django.conf import settings
# Добавляем валидаторы
from django.core.validators import MinValueValidator, MaxValueValidator


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        'Название ингредиента',
        max_length=128,  # Из спецификации
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64,  # Из спецификации
        help_text='Введите единицу измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        help_text='Автор рецепта'
    )
    name = models.CharField(
        'Название рецепта',
        max_length=256,  # Из спецификации
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
        help_text='Загрузите изображение рецепта'
        # blank=True, null=True # В спецификации поле image обязательное при создании
    )
    text = models.TextField(
        'Описание рецепта',
        help_text='Введите описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты для рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин.)',
        validators=[
            MinValueValidator(
                1, message='Время приготовления должно быть не менее 1 минуты'
            ),
            MaxValueValidator(
                32000, message='Слишком большое время приготовления'
            )
        ],
        help_text='Укажите время приготовления в минутах'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True  # Индекс для быстрой сортировки по дате
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']  # Сортировка от новых к старым по умолчанию

    def __str__(self):
        return f'{self.name} (автор: {self.author.username})'


class IngredientInRecipe(models.Model):
    """Модель для связи ингредиентов и рецептов с указанием количества."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',  # Обратная связь от Recipe
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,  # При удалении ингредиента удаляем связь
        related_name='recipe_ingredients',  # Обратная связь от Ingredient
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                1, message='Количество должно быть не менее 1'
            ),
            MaxValueValidator(
                32000, message='Слишком большое количество'
            )
        ],
        help_text='Укажите количество ингредиента'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} ({self.amount} '
                f'{self.ingredient.measurement_unit}) в "{self.recipe.name}"')


class Favorite(models.Model):
    """Модель для добавления рецептов в избранное пользователя."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',  # Кто добавил в избранное
        verbose_name='Избранный рецепт'
    )
    added_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-added_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'"{self.recipe.name}" в избранном у {self.user.username}'


class ShoppingCart(models.Model):
    """Модель для добавления рецептов в список покупок пользователя."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart_of',  # Чей список покупок
        verbose_name='Рецепт в списке покупок'
    )
    added_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['-added_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shopping_cart_recipe'
            )
        ]

    def __str__(self):
        return f'"{self.recipe.name}" в списке покупок у {self.user.username}'
