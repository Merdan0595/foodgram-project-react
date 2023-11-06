from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.permissions import (AllowAny, IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.decorators import action
from rest_framework.response import Response
from djoser.views import UserViewSet

from recipes.models import (Ingredient, Tag, Recipe, Follow,
                            Favorite, ShoppingCart, RecipeIngredient)
from users.models import User
from users.serializers import ProfileSerializer, UserSerializer
from .serializers import (IngredientSerializer, TagSerializer,
                          RecipeListSerializer, RecipeSerializer,
                          FollowListSerializer, FollowSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)
from .filters import RecipeFilter


def error_404_view(request, exception):
    """Обработчик ошибки 404."""
    return render(request, '404.html', status=HttpResponseNotFound)


def custom_action(self, request, pk=None):
    """Функция для списка покупок/подписок."""
    recipe_or_following = self.get_object()
    current_user = request.user
    if self.action == 'shopping_cart':
        model_class = ShoppingCart
        message_create_validate = 'Рецепт уже в списке покупок'
        message_delete_validate = 'Рецепт не найден в списке покупок'
    else:
        model_class = Follow
        message_create_validate = 'Вы уже подписаны на данного пользователя'
        message_delete_validate = 'Пользователь не найден в подписках'

    if request.method == 'POST':
        if not model_class.objects.filter(
            user=current_user, pk=recipe_or_following.pk
        ).exists():
            instance = model_class.objects.create(
                user=current_user, pk=recipe_or_following.pk
            )
            serializer = self.get_serializer(instance=instance)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        else:
            return Response({'message': message_create_validate},
                            status=status.HTTP_400_BAD_REQUEST)

    else:
        try:
            instance = model_class.objects.get(
                user=current_user, pk=recipe_or_following.pk
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model_class.DoesNotExist:
            return Response(
                {'message': message_delete_validate},
                status=status.HTTP_400_BAD_REQUEST
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тэгов."""
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для рецептов.

    :def favorite: Добавить(удалить) в избранное.
    :def shopping_cart: Добавить(удалить) в список покупок.
    :def download_shopping_cart: Скачать список покупок.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if not user.favorite.filter(pk=recipe.pk).exists():
            favorite = Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(instance=favorite)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        else:
            return Response({'message': 'Рецепт уже в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        try:
            favorite = Favorite.objects.get(user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response(
                {'message': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        custom_action(request=request, pk=pk)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        if not request.user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        items = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount_sum=Sum('amount'))
        )
        shopping_cart_text = "Shopping Cart\n"
        for item in items:
            ingredient_name = item['ingredient__name']
            measurement_unit = item['ingredient__measurement_unit']
            amount = item['amount_sum']
            shopping_cart_text += (
                f"{ingredient_name} ({measurement_unit}) - {amount}\n"
            )
        response = HttpResponse(shopping_cart_text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class UsersViewSet(UserViewSet):
    """
    Вьюсет для пользователей.

    :def subscriptions: Список подписчиков.
    :def subscribe: Подписаться/отписаться.
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action in ['subscriptions', 'subscribe']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSerializer
        elif self.action == 'subscribe':
            return FollowSerializer
        elif self.action == 'subscriptions':
            return FollowListSerializer
        return super().get_serializer_class()

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=self.request.user)
        serializer = FollowListSerializer(subscriptions, many=True,
                                          context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        custom_action(request=request, pk=pk)
