from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("author",)

    def _filter_user_relation(self, queryset, name, value, related_manager):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(**{f"{related_manager}__user": user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_user_relation(
            queryset, name, value, "favorited_by"
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_user_relation(
            queryset, name, value, "in_shopping_cart_of"
        )
