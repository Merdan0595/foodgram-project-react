from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import (RecipeViewSet, TagViewSet,
                    IngredientViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', UsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
