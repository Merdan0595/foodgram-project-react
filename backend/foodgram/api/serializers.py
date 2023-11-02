import base64
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Recipe, RecipeIngredient,
                            Ingredient, Tag, Follow, Favorite,
                            ShoppingCart)
from users.models import User
from users.serializers import ProfileSerializer


MIN_VALUE = 1


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    "Сериализатор для ингредиентов"
    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'measurement_unit',
        )


class AddIngredientSerializer(serializers.ModelSerializer):
    "Вложенный сериализатор для добавления ингредиентов при создании рецепта"
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientAmountSerializer(serializers.ModelSerializer):
    "Вложенный сериализатор для отображения ингредиентов в рецепте"
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )

    def validate(self, data):
        if data.get('amount') < 1:
            raise serializers.ValidationError(
                'Количество не может быть меньше 1'
            )
        return data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeListSerializer(serializers.ModelSerializer):
    "Сериализатор для списка рецептов"
    ingredients = IngredientAmountSerializer(source='recipeingredient_set',
                                             many=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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
    "Сериализатор для создания рецепта"
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = ProfileSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'author', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Минимум один ингридиент обязателен!'}
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

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        request = self.context.get('request')
        author = request.user
        recipe = Recipe.objects.create(author=author, **validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'])

        recipe.tags.set(tags_data)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        ingredients_data = validated_data.get('ingredients')
        if ingredients_data:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance, **ingredient_data
                )
        tags_data = validated_data.get('tags')
        if tags_data:
            instance.tags.set(tags_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class FollowFavoriteRecipeSerializer(serializers.ModelSerializer):
    "Вложенный сериализатор для списка подписок/избранного"
    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )


class FollowListSerializer(serializers.ModelSerializer):
    "Сериализатор для списка подписок"
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    is_subscribed = serializers.BooleanField(default=True)
    email = serializers.ReadOnlyField(source='following.email')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    id = serializers.ReadOnlyField(source='following.id')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.following)
        return FollowFavoriteRecipeSerializer(
            recipes, many=True, context=self.context
        ).data


class FollowSerializer(serializers.ModelSerializer):
    "Сериализатор для подписки"
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
            instance.following, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    "Сериализатор для избранного"
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return FollowFavoriteRecipeSerializer(
            instance.favorited, context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    "Сериализатор для списка покупок"
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return FollowFavoriteRecipeSerializer(
            instance.in_shopping_cart, context=self.context
        ).data
