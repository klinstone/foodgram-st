from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, CustomUserViewSet

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')

router.register('ingredients', IngredientViewSet, basename='ingredients')

router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
]
