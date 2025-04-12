# backend/api/serializers.py
import base64 # Для декодирования base64 картинок
from django.core.files.base import ContentFile # Для создания файла из строки
from django.db import transaction # Для атомарных операций с БД
from django.shortcuts import get_object_or_404 # Для получения объектов
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer

# Импортируем наши модели
from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart
)
from users.models import User, Subscription


# --- Сериализаторы для Ингредиентов ---

class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit') # Ингредиенты только читаются через API


# --- Сериализаторы для Пользователей ---

class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор для модели Пользователя (чтение)."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    # avatar = serializers.ImageField(read_only=True) # Djoser сам добавит аватар, если он есть в модели

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar' # Добавляем is_subscribed и avatar
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора `obj`."""
        user = self.context.get('request').user
        # Если пользователь анонимный или это его собственный профиль
        if not user or user.is_anonymous:
            return False
        # Проверяем наличие подписки
        return Subscription.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для создания Пользователя (регистрация)."""
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password', 'id'
        ) # Добавляем id для ответа 201 по спецификации

# --- Сериализаторы для Рецептов (вспомогательные) ---

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """
    Сериализатор для обработки ингредиентов при создании/обновлении рецепта.
    Ожидает id ингредиента и его количество.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1, max_value=32000) # Валидация количества

    def validate_id(self, value):
        """Проверяет, существует ли ингредиент с таким id."""
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Ингредиент с id={value} не найден."
            )
        return value


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки изображений в формате Base64."""
    def to_internal_value(self, data):
        # Проверяем, что пришла строка и она содержит data:image
        if isinstance(data, str) and data.startswith('data:image'):
            # Разделяем строку на формат и само содержимое base64
            format, imgstr = data.split(';base64,')
            # Получаем расширение файла
            ext = format.split('/')[-1]
            # Декодируем base64 строку и создаем ContentFile
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


# --- Сериализаторы для Рецептов (основные) ---

class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов (список и детальный)."""
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients' # Используем related_name из IngredientInRecipe
    )
    # tags = TagSerializer(many=True, read_only=True) # Если бы были теги
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(read_only=True) # Для чтения используем стандартный ImageField

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', # 'tags',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time'
        )

    def _get_user_relation(self, obj, related_manager_name):
        """Вспомогательный метод для проверки связи пользователя с рецептом."""
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        # Проверяем через соответствующий менеджер ('favorites' или 'shopping_cart')
        manager = getattr(user, related_manager_name)
        return manager.filter(recipe=obj).exists()

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""
        return self._get_user_relation(obj, 'favorites') # related_name из Favorite

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок текущим пользователем."""
        return self._get_user_relation(obj, 'shopping_cart') # related_name из ShoppingCart


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    ingredients = RecipeIngredientCreateSerializer(many=True)
    author = CustomUserSerializer(read_only=True) # Автор определяется автоматически
    image = Base64ImageField(required=True) # Используем кастомное поле
    # tags = serializers.PrimaryKeyRelatedField( # Если бы были теги
    #     queryset=Tag.objects.all(), many=True
    # )
    cooking_time = serializers.IntegerField(min_value=1, max_value=32000)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', # 'tags',
            'image', 'name', 'text', 'cooking_time', 'author'
        )
        read_only_fields = ('id', 'author')

    def validate_ingredients(self, value):
        """Проверяет ингредиенты: не пустые, без дубликатов."""
        if not value:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один ингредиент."
            )
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return value

    # def validate_tags(self, value): # Если бы были теги
    #     """Проверяет теги: не пустые, без дубликатов."""
    #     if not value:
    #         raise serializers.ValidationError("Нужно выбрать хотя бы один тег.")
    #     if len(value) != len(set(value)):
    #         raise serializers.ValidationError("Теги не должны повторяться.")
    #     return value

    def _create_ingredients(self, recipe, ingredients_data):
        """Создает связи ингредиентов с рецептом."""
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ing_data['id'],
                amount=ing_data['amount']
            ) for ing_data in ingredients_data
        ])

    @transaction.atomic # Гарантирует, что все операции либо выполнятся, либо откатятся
    def create(self, validated_data):
        """Создает новый рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop('ingredients')
        # tags_data = validated_data.pop('tags') # Если бы были теги

        # Устанавливаем автора из запроса
        validated_data['author'] = self.context.get('request').user

        recipe = Recipe.objects.create(**validated_data)
        # recipe.tags.set(tags_data) # Если бы были теги
        self._create_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        # Обработка ингредиентов: удаляем старые, создаем новые
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.ingredients.clear() # Удаляем старые связи через M2M
            self._create_ingredients(instance, ingredients_data)

        # Обработка тегов: если они переданы, обновляем
        # tags_data = validated_data.pop('tags', None) # Если бы были теги
        # if tags_data is not None:
        #     instance.tags.set(tags_data)

        # Обновляем остальные поля рецепта
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """После создания/обновления возвращает представление для чтения."""
        # Используем RecipeReadSerializer для ответа
        return RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Урезанный сериализатор рецепта (для избранного, подписок и т.п.)."""
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


# --- Сериализаторы для Подписок ---

class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для вывода подписок (пользователи + их рецепты)."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = CustomUserSerializer.Meta.fields # Все поля от юзера только для чтения

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        return obj.recipes.count() # Используем related_name='recipes' из модели Recipe

    def get_recipes(self, obj):
        """Возвращает список рецептов автора с ограничением по лимиту."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all() # Получаем все рецепты автора

        if limit:
            try:
                limit_int = int(limit)
                recipes = recipes[:limit_int] # Применяем лимит
            except ValueError:
                # Если limit не число, игнорируем его
                pass

        # Сериализуем рецепты с урезанным сериализатором
        serializer = RecipeMinifiedSerializer(recipes, many=True, read_only=True)
        return serializer.data
