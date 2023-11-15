from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

from users.models import User
from .constants import REGEX, MIN_NUMBER


class Tag(models.Model):
    """Модель тэга."""
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(
        max_length=200,
        validators=[RegexValidator(regex=REGEX)],
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
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
    name = models.CharField(max_length=200)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_NUMBER)]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связь рецепта с ингредиентами с добавлением количества."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_NUMBER)]
    )


class Follow(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            )
        ]


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorite')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorited')

    class Meta:
        verbose_name = 'Избранное'
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='in_shopping_cart')

    class Meta:
        verbose_name = 'Список покупок'
        unique_together = ('user', 'recipe')
