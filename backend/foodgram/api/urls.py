from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (RecipeViewSet, TagViewSet,
                    IngredientViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', UsersViewSet,
                basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
