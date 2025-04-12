from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Импорты для вьюсетов
from .views import IngredientViewSet, RecipeViewSet, CustomUserViewSet

# Создаем router и регистрируем ViewSets
router = DefaultRouter()

# Регистрируем маршруты для пользователей (используем наш кастомный вьюсет)
# Префикс 'users' будет обработан этим роутером
router.register('users', CustomUserViewSet, basename='users')

# Регистрируем маршруты для ингредиентов
router.register('ingredients', IngredientViewSet, basename='ingredients')

# Регистрируем маршруты для рецептов
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    # Подключаем созданные роутером URL
    path('', include(router.urls)),
    # URL для стандартной аутентификации Django (login/logout в Browsable API DRF)
    # path('auth/', include('rest_framework.urls')), # если нужен Browsable API login
]