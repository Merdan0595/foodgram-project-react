from django.http import HttpResponse
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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    "Вьюсет для ингредиентов"
    "доступен только для чтения"
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    "Вьюсет для тэгов"
    "доступен только для чтения"
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    "Вьюсет для рецептов"
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'is_favorited', 'author', 'in_shopping_cart', 'tags'
    )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if not user.favorite.filter(pk=recipe.pk).exists():
                favorite = Favorite.objects.create(user=user, recipe=recipe)
                serializer = FavoriteSerializer(favorite)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response({'message': 'Рецепт уже в избранном'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
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
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if not user.shopping_cart.filter(pk=recipe.pk).exists():
                shopping_cart = ShoppingCart.objects.create(
                    user=user, recipe=recipe
                )
                serializer = ShoppingCartSerializer(shopping_cart)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response({'message': 'Рецепт уже в списке покупок'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                shopping_cart = ShoppingCart.objects.get(
                    user=user, recipe=recipe
                )
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'message': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
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
    "Вьюсет для пользователей"
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
        subscriptions = self.request.user.follower.all()
        serializer = FollowListSerializer(subscriptions, many=True,
                                          context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, *args, **kwargs):
        user_to_subscribe = self.get_object()
        current_user = request.user
        if request.method == 'POST':
            if not current_user.follower.filter(
                    following=user_to_subscribe).exists():
                Follow.objects.create(
                    user=current_user, following=user_to_subscribe
                )
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Пользователь уже подписан'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            if current_user.follower.filter(
                    following=user_to_subscribe).exists():
                current_user.follower.get(following=user_to_subscribe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'message': 'Пользователь не найден в подписках'},
                    status=status.HTTP_400_BAD_REQUEST)
