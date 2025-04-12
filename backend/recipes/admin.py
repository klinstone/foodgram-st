# backend/recipes/admin.py
from django.contrib import admin
from .models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart
)

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административная панель для модели Ingredient."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',) # Поиск по названию
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'


# Inline модель для редактирования ингредиентов прямо на странице рецепта
class IngredientInRecipeInline(admin.TabularInline):
    """Inline для редактирования ингредиентов в рецепте."""
    model = IngredientInRecipe
    extra = 1 # Количество пустых форм для добавления
    min_num = 1 # Минимальное количество ингредиентов
    autocomplete_fields = ('ingredient',) # Удобный поиск ингредиентов


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель для модели Recipe."""
    list_display = ('id', 'name', 'author', 'cooking_time', 'pub_date', 'favorited_count')
    search_fields = ('name', 'author__username') # Поиск по названию и автору
    list_filter = ('author', 'name', 'pub_date') # Фильтры
    readonly_fields = ('pub_date', 'favorited_count') # Поля только для чтения
    inlines = (IngredientInRecipeInline,) # Подключаем inline для ингредиентов
    empty_value_display = '-пусто-'

    def favorited_count(self, obj):
        """Вычисляет количество добавлений рецепта в избранное."""
        return obj.favorited_by.count() # Используем related_name 'favorited_by' из модели Favorite

    favorited_count.short_description = 'В избранном (раз)' # Название колонки


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Административная панель для модели IngredientInRecipe (в основном для отладки)."""
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    autocomplete_fields = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административная панель для модели Favorite."""
    list_display = ('id', 'user', 'recipe', 'added_date')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_date',)
    autocomplete_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административная панель для модели ShoppingCart."""
    list_display = ('id', 'user', 'recipe', 'added_date')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_date',)
    autocomplete_fields = ('user', 'recipe')