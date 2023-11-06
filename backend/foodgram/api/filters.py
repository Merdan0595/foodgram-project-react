from django_filters.rest_framework import (ModelMultipleChoiceFilter,
                                           FilterSet, BooleanFilter,
                                           NumberFilter)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """Кастомный фильтр для рецепта."""
    author = NumberFilter(field_name='author')
    tags = ModelMultipleChoiceFilter(field_name='tags__slug',
                                     to_field_name='slug',
                                     queryset=Tag.objects.all())
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'author', 'is_in_shopping_cart')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        else:
            return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited__user=self.request.user)
        else:
            return queryset
