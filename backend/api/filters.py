# backend/api/filters.py
from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient
# from tags.models import Tag # Если бы были теги

class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов по началу названия."""
    # Имя параметра в URL будет 'name'
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов: по автору, тегам, избранному, списку покупок."""
    # tags = filters.ModelMultipleChoiceFilter( # Если бы были теги
    #     field_name='tags__slug',
    #     to_field_name='slug',
    #     queryset=Tag.objects.all(),
    # )
    author = filters.NumberFilter(field_name='author__id')  # Фильтр по ID автора
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        # Поля, по которым можно фильтровать напрямую
        fields = ('author', )

    def _filter_user_relation(self, queryset, name, value, related_manager):
        """Общий метод для фильтрации по 'is_favorited' и 'is_in_shopping_cart'."""
        user = self.request.user
        if value and user.is_authenticated:
            # Фильтруем рецепты, которые есть в related_manager текущего пользователя
            return queryset.filter(**{f'{related_manager}__user': user})
        # Если value=False или пользователь не аутентифицирован, не фильтруем
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по наличию в избранном у текущего пользователя."""
        return self._filter_user_relation(queryset, name, value, 'favorited_by')
        # 'favorited_by' - related_name из модели Favorite к Recipe

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по наличию в списке покупок у текущего пользователя."""
        return self._filter_user_relation(queryset, name, value, 'in_shopping_cart_of')
         # 'in_shopping_cart_of' - related_name из модели ShoppingCart к Recipe
