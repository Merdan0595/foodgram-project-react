from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

from users.models import User

REGEX = r'^[-a-zA-Z0-9_]+$'
MIN_NUMBER = 1


class Tag(models.Model):
    "Модель для Тэга"
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(
        max_length=200,
        validators=[RegexValidator(regex=REGEX)],
        unique=True
    )
    REQUIRED_FIELDS = ('name', 'color', 'slug')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    "Модель ингредиента"
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)
    REQUIRED_FIELDS = ('name', 'measurement_unit')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    "Модель рецепта"
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
        )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='recipe_ingredients'
        )
    tags = models.ManyToManyField(
        Tag, related_name='recipes'
        )
    image = models.ImageField(upload_to='image/')
    name = models.CharField(max_length=250)
    text = models.TextField()
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(MIN_NUMBER)]
        )
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)


class RecipeIngredient(models.Model):
    "Связь рецепта с ингредиентами с добавлением количества"
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField(
        validators=[MinValueValidator(MIN_NUMBER)]
    )


class Follow(models.Model):
    "Модель подписки"
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorited')

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='in_shopping_cart')

    class Meta:
        unique_together = ('user', 'recipe')
