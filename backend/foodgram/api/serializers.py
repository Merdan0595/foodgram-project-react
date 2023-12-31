import base64

from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Recipe, RecipeIngredient,
                            Ingredient, Tag, Follow, Favorite,
                            ShoppingCart)
from users.models import User
from users.serializers import ProfileSerializer
from recipes.constants import MIN_NUMBER


class Base64ImageField(serializers.ImageField):
    """Конвертер base64 в файл."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'measurement_unit',
        )


class AddIngredientSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для добавления ингредиентов в рецепт."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_NUMBER)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для отображения ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    ingredients = IngredientAmountSerializer(source='recipeingredient_set',
                                             many=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    author = ProfileSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'author', 'image', 'name',
            'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return request.user.is_authenticated and obj.favorited.filter(
            user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return request.user.is_authenticated and obj.in_shopping_cart.filter(
            user=request.user).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = ProfileSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'author', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Минимум один ингредиент обязателен!'}
            )

        ingredient_ids = []

        for ingredient in ingredients:
            ingredient_ids.append(ingredient['id'])
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты повторяются'}
            )

        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Минимум один тег обязателен!'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({'tags': 'Теги не уникальны'})
        return tags

    def bulk_ingredients(self, ingredients_data, recipe):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            ))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        request = self.context.get('request')
        author = request.user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.bulk_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        if ingredients_data is None or tags_data is None:
            raise serializers.ValidationError(
                {'error':
                 'Теги и ингредиенты необходимы для обновления рецепта'}
            )
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.bulk_ingredients(ingredients_data, instance)
        if tags_data:
            instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class FollowFavoriteRecipeSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для списка подписок/избранного."""
    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )


class FollowListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        return FollowFavoriteRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, following=obj
            ).exists()
        return False


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""
    following = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        if Follow.objects.filter(
            user=self.context['request'].user,
            following=data['following']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного автора!'
            )
        return data

    def to_representation(self, instance):
        return FollowListSerializer(
            instance['following'], context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return FollowFavoriteRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return FollowFavoriteRecipeSerializer(
            instance.recipe, context=self.context
        ).data
