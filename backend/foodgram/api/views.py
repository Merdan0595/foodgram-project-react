from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.permissions import (AllowAny, IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet

from recipes.models import (Ingredient, Tag, Recipe, Follow,
                            Favorite, ShoppingCart, RecipeIngredient)
from users.models import User
from users.serializers import ProfileSerializer, UserSerializer
from .permissions import IsRecipeAuthor
from .serializers import (IngredientSerializer, TagSerializer,
                          RecipeListSerializer, RecipeSerializer,
                          FollowListSerializer, FollowSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)
from .filters import RecipeFilter, IngredientFilter


def error_404_view(request, exception):
    """Обработчик ошибки 404."""
    return render(request, '404.html', status=HttpResponseNotFound)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
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
    permission_classes = (IsAuthenticatedOrReadOnly, IsRecipeAuthor)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    def add_favorite_or_shopping_cart(self, request, is_favorite):
        recipe = self.get_object()
        user = request.user
        queryset = user.favorite if is_favorite else user.shopping_cart
        model = Favorite if is_favorite else ShoppingCart
        serializer = (
            FavoriteSerializer if is_favorite else ShoppingCartSerializer
        )
        message = ('Рецепт уже в избранном' if is_favorite
                   else 'Рецепт уже в списке покупок')
        if not queryset.filter(pk=recipe.pk).exists():
            favorite = model.objects.create(user=user, recipe=recipe)
            serializer = serializer(instance=favorite)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        else:
            return Response({'message': message},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete_favorite_or_shopping_cart(self, request, is_favorite):
        recipe = self.get_object()
        user = request.user
        model = Favorite if is_favorite else ShoppingCart
        message = ('Рецепт не найден в избранном' if is_favorite
                   else 'Рецепт не найден в списке покупок')
        try:
            to_delete = model.objects.get(user=user, recipe=recipe)
            to_delete.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response(
                {'message': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        return self.add_favorite_or_shopping_cart(request, is_favorite=True)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_favorite_or_shopping_cart(request, is_favorite=True)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        return self.add_favorite_or_shopping_cart(request, is_favorite=False)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_favorite_or_shopping_cart(
            request, is_favorite=False
        )

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
        elif self.action in ['subscriptions', 'subscribe', 'me']:
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
        detail=False, methods=['get', 'list'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=self.request.user)
        paginator = LimitOffsetPagination()
        subscriptions_paginated = paginator.paginate_queryset(
            subscriptions, request
        )
        serializer = FollowListSerializer(
            subscriptions_paginated, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        user_to_subscribe = self.get_object()
        current_user = request.user
        serializer = FollowSerializer(data={'user': current_user.id,
                                            'following': user_to_subscribe.id},
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        if not current_user.follower.filter(following=user_to_subscribe
                                            ).exists():
            Follow.objects.create(
                user=current_user, following=user_to_subscribe
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Пользователь уже подписан'},
                            status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        user_to_subscribe = self.get_object()
        current_user = request.user
        if current_user.follower.filter(following=user_to_subscribe).exists():
            current_user.follower.get(following=user_to_subscribe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'Пользователь не найден в подписках'},
                            status=status.HTTP_400_BAD_REQUEST)
