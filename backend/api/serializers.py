from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    Ingredient,
    IngredientInRecipe,
    Recipe,
)
from users.models import User


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ("is_subscribed", "avatar")

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.following.filter(author=obj).exists()
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
        error_messages={
            "min_value": f"Количество должно быть не меньше"
            f"{MIN_INGREDIENT_AMOUNT}.",
            "max_value": f"Количество должно быть не больше"
            f"{MAX_INGREDIENT_AMOUNT}.",
        },
    )


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and user.shopping_cart.filter(recipe=obj).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=False)
    ingredients = RecipeIngredientCreateSerializer(
        many=True, allow_empty=False
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        error_messages={
            "min_value": f"Время готовки должно быть не меньше"
            f"{MIN_COOKING_TIME} мин.",
            "max_value": f"Время готовки должно быть не больше"
            f"{MAX_COOKING_TIME} мин.",
        },
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
            "author",
        )
        read_only_fields = ("id", "author")

    def validate(self, data):
        """Общая валидация данных рецепта."""
        ingredients = data.get("ingredients")

        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError(
                    {"ingredients": "Нужно добавить хотя бы один ингредиент."}
                )

            ingredient_ids = [item["id"].id for item in ingredients]
            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    {"ingredients": "Ингредиенты не должны повторяться."}
                )

        image = data.get("image")
        if self.instance is None and not image:
            raise serializers.ValidationError(
                {"image": "Необходимо загрузить изображение."}
            )

        return data

    def _set_ingredients(self, recipe, ingredients_data):
        """Вспомогательный метод для создания/обновления ингредиентов."""
        if self.instance:
            recipe.ingredients.clear()

        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ing_data["id"],
                    amount=ing_data["amount"],
                )
                for ing_data in ingredients_data
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        image = validated_data.pop("image")

        validated_data["author"] = self.context.get("request").user

        recipe = Recipe.objects.create(**validated_data)

        recipe.image = image

        self._set_ingredients(recipe, ingredients_data)

        recipe.save()
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        image = validated_data.pop("image", None)

        if ingredients_data is not None:
            self._set_ingredients(instance, ingredients_data)

        if image is not None:
            instance.image = image

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Используем ReadSerializer для вывода
        данных после создания/обновления."""
        return RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()

        if limit:
            try:
                recipes = recipes[: int(limit)]
            except (ValueError, TypeError):
                pass

        serializer = RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.Serializer):
    avatar = serializers.ImageField(read_only=True)
