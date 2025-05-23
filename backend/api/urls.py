from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()

router.register("users", CustomUserViewSet, basename="users")

router.register("ingredients", IngredientViewSet, basename="ingredients")

router.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [
    path("", include(router.urls)),
]
