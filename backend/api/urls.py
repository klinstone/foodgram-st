from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Импорты для вьюсетов будут добавлены позже
# from .views import IngredientViewSet, TagViewSet, RecipeViewSet, UserViewSet

# Создаем router и регистрируем ViewSets
router = DefaultRouter()

# Регистрация будет добавлена позже, когда создадим ViewSets
# router.register('ingredients', IngredientViewSet, basename='ingredients')
# router.register('tags', TagViewSet, basename='tags')
# router.register('recipes', RecipeViewSet, basename='recipes')
# router.register('users', UserViewSet, basename='users')


urlpatterns = [
    # Подключаем созданные роутером URL
    path('', include(router.urls)),
]