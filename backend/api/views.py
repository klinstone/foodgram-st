# backend/api/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse # Для скачивания файла
from django.db.models import Sum # Для агрегации ингредиентов
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet # Импортируем базовый вьюсет Djoser

# Наши модели
from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart
)
from users.models import User, Subscription

# Наши сериализаторы, фильтры и пермишены
from .serializers import (
    IngredientSerializer, RecipeReadSerializer, RecipeCreateUpdateSerializer,
    CustomUserSerializer, SubscriptionSerializer, RecipeMinifiedSerializer
)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра ингредиентов.
    Доступен всем пользователям. Реализован поиск по имени.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,) # Разрешаем доступ всем
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None # Отключаем пагинацию для ингредиентов


class CustomUserViewSet(DjoserUserViewSet):
    """
    ViewSet для работы с Пользователями (расширяет Djoser).
    Включает подписки.
    """
    # queryset уже определен в DjoserUserViewSet (User.objects.all())
    # serializer_class будет определен Djoser в зависимости от action
    # permission_classes тоже управляются Djoser (или можно переопределить)
    # pagination_class использует настройки из settings.REST_FRAMEWORK

    @action(
        detail=False, # Не для конкретного пользователя, а для /users/subscriptions/
        methods=['get'],
        permission_classes=[IsAuthenticated] # Только для авторизованных
    )
    def subscriptions(self, request):
        """Возвращает пользователей, на которых подписан текущий пользователь."""
        # Получаем авторов, на которых подписан текущий user
        authors = User.objects.filter(following__user=request.user)
        # Пагинируем результат
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, # Для конкретного пользователя /users/{id}/subscribe/
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated] # Только для авторизованных
    )
    def subscribe(self, request, id=None):
        """Подписывает/отписывает текущего пользователя на/от пользователя с id."""
        if not id: # Доп. проверка, хотя URL должен содержать id
             return Response(
                {'detail': 'ID пользователя не указан.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        author = get_object_or_404(User, id=id)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription_exists = Subscription.objects.filter(
            user=user, author=author
        ).exists()

        if request.method == 'POST':
            if subscription_exists:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not subscription_exists:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = get_object_or_404(Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # На случай если добавят другие методы
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с Рецептами.
    Поддерживает CRUD, фильтрацию, избранное, список покупок, скачивание.
    """
    queryset = Recipe.objects.all()
    # Права доступа: Чтение для всех, остальное - для владельца или админа/ридонли
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter) # Добавляем сортировку
    filterset_class = RecipeFilter
    ordering_fields = ['name', 'pub_date', 'cooking_time'] # Поля для сортировки
    ordering = ['-pub_date'] # Сортировка по умолчанию

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        # Для create, update, partial_update используем один сериализатор
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        """При создании рецепта автором назначается текущий пользователь."""
        serializer.save(author=self.request.user)

    def _manage_user_recipe_relation(self, request, pk, related_model, error_msg_exists, error_msg_not_exists):
        """Общий метод для добавления/удаления рецепта в избранное/корзину."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = related_model.objects.filter(user=user, recipe=recipe).exists()

        if request.method == 'POST':
            if relation_exists:
                return Response(
                    {'errors': error_msg_exists},
                    status=status.HTTP_400_BAD_REQUEST
                )
            related_model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not relation_exists:
                return Response(
                    {'errors': error_msg_not_exists},
                    status=status.HTTP_400_BAD_REQUEST
                )
            relation = get_object_or_404(related_model, user=user, recipe=recipe)
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated] # Только авторизованные
    )
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт из избранного."""
        return self._manage_user_recipe_relation(
            request, pk, Favorite,
            'Рецепт уже в избранном.',
            'Рецепта не было в избранном.'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated] # Только авторизованные
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт из списка покупок."""
        return self._manage_user_recipe_relation(
            request, pk, ShoppingCart,
            'Рецепт уже в списке покупок.',
            'Рецепта не было в списке покупок.'
        )

    @action(
        detail=False, # Не для конкретного рецепта
        methods=['get'],
        permission_classes=[IsAuthenticated] # Только авторизованные
    )
    def download_shopping_cart(self, request):
        """Формирует и отдает файл со списком покупок."""
        user = request.user
        # Получаем ID рецептов в корзине пользователя
        recipe_ids = ShoppingCart.objects.filter(user=user).values_list('recipe__id', flat=True)

        if not recipe_ids:
            return Response(
                 {'errors': 'Список покупок пуст.'},
                 status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем все ингредиенты из этих рецептов, агрегируем количество
        ingredients = IngredientInRecipe.objects.filter(
            recipe__id__in=recipe_ids
        ).values(
            'ingredient__name', # Группируем по имени
            'ingredient__measurement_unit' # и единице измерения
        ).annotate(
            total_amount=Sum('amount') # Суммируем количество
        ).order_by('ingredient__name') # Сортируем по имени

        # Формируем текстовое содержимое файла
        shopping_list_content = "Список покупок для Foodgram:\n\n"
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            shopping_list_content += f"- {name} ({unit}) — {amount}\n"

        # Создаем HTTP ответ с файлом
        response = HttpResponse(shopping_list_content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    # Эндпоинт get-link не реализован, т.к. спецификация неясна
    # по механизму генерации короткой ссылки.
    # Можно просто вернуть полный URL рецепта, если потребуется.
    # @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    # def get_link(self, request, pk=None):
    #     recipe = self.get_object()
    #     # Здесь можно реализовать логику генерации короткой ссылки
    #     # Пока просто вернем абсолютный URL до API эндпоинта рецепта
    #     link = request.build_absolute_uri(recipe.get_absolute_url()) # если есть метод get_absolute_url
    #     # или просто link = request.build_absolute_uri()
    #     return Response({'short-link': link}, status=status.HTTP_200_OK)