from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart)
from rest_framework import filters as drf_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeMinifiedSerializer, RecipeReadSerializer,
                          SetAvatarSerializer, SubscriptionSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class CustomUserViewSet(DjoserUserViewSet):

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        if not id:
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
            subscription = get_object_or_404(
                Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        serializer_class=SetAvatarSerializer
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            avatar_file = serializer.validated_data.get('avatar')

            if user.avatar:
                user.avatar.delete(save=False)

            user.avatar = avatar_file
            user.save(update_fields=['avatar'])

            user_serializer = CustomUserSerializer(
                user, context={'request': request})
            return Response(user_serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if not user.avatar:
                return Response(
                    {'errors': 'У пользователя нет аватара для удаления.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar.delete(save=True)

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter)
    filterset_class = RecipeFilter
    ordering_fields = ['name', 'pub_date', 'cooking_time']
    ordering = ['-pub_date']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _manage_user_recipe_relation(self, request, pk, related_model,
                                     error_msg_exists, error_msg_not_exists):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = related_model.objects.filter(
            user=user, recipe=recipe).exists()

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
            relation = get_object_or_404(
                related_model, user=user, recipe=recipe)
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self._manage_user_recipe_relation(
            request, pk, Favorite,
            'Рецепт уже в избранном.',
            'Рецепта не было в избранном.'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self._manage_user_recipe_relation(
            request, pk, ShoppingCart,
            'Рецепт уже в списке покупок.',
            'Рецепта не было в списке покупок.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipe_ids = ShoppingCart.objects.filter(
            user=user).values_list('recipe__id', flat=True)

        if not recipe_ids:
            return Response(
                {'errors': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = IngredientInRecipe.objects.filter(
            recipe__id__in=recipe_ids
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list_content = "Список покупок для Foodgram:\n\n"
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            shopping_list_content += f"- {name} ({unit}) — {amount}\n"

        response = HttpResponse(shopping_list_content,
                                content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response
