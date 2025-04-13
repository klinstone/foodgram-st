import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer
)
from rest_framework import serializers

from recipes.models import Ingredient, IngredientInRecipe, Recipe
from users.models import Subscription, User


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class CustomUserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password', 'id'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=1, max_value=32000)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Ингредиент с id={value} не найден."
            )
        return value


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time'
        )

    def _get_user_relation(self, obj, related_manager_name):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        manager = getattr(user, related_manager_name)
        return manager.filter(recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self._get_user_relation(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        return self._get_user_relation(obj, 'shopping_cart')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1, max_value=32000)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients',
            'image', 'name', 'text', 'cooking_time', 'author'
        )
        read_only_fields = ('id', 'author')

    def validate_ingredients(self, value):
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

    def _create_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ing_data['id'],
                amount=ing_data['amount']
            ) for ing_data in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context.get('request').user

        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.ingredients.clear()
            self._create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + \
            ('recipes', 'recipes_count')
        read_only_fields = CustomUserSerializer.Meta.fields

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if limit:
            try:
                limit_int = int(limit)
                recipes = recipes[:limit_int]
            except ValueError:
                pass

        serializer = RecipeMinifiedSerializer(
            recipes, many=True, read_only=True)
        return serializer.data


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)
