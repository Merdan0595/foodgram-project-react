from django.contrib import admin

from .models import Ingredient, Tag, RecipeIngredient, Recipe


class BaseAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    pass


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    pass


class RecipeIngredientsAdmin(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'cooking_time',
                    'get_ingredients')
    list_display_links = ('name',)
    inlines = (RecipeIngredientsAdmin,)

    def get_ingredients(self, obj):
        queryset = RecipeIngredient.objects.filter(recipe_id=obj.id).all()
        return ', '.join(
            [f' {item.ingredient.name} {item.amount} '
             f'{item.ingredient.measurement_unit}' for item in queryset])
