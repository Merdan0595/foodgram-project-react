from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import (RecipeViewSet, TagViewSet,
                    IngredientViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users/(?P<user_id>\d+)/subcribe',
                UsersViewSet,
                basename='subscribe')
router.register(r'subscriptions', UsersViewSet,
                basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
