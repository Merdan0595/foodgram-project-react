from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView

from .views import (RecipeViewSet, TagViewSet, FavoriteView,
                    IngredientViewSet)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                FavoriteView, basename='favorite')
router.register(r'ingredients', IngredientViewSet)
# router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',)

# router.register(r'posts', PostViewSet)
# router.register(r'groups', GroupViewSet)
# router.register(r'posts/(?P<post_id>\d+)/comments',
#                 CommentViewSet,
#                 basename='comments')
# router.register(r'follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/token/login/', TokenCreateView.as_view(),
         name='token_create'),
    path('auth/token/logout/', TokenDestroyView.as_view(),
         name='token_destroy'),
]
