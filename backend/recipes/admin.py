from django.contrib import admin
from recipes.models import (FollowOnRecipe, FollowOnUser, Ingredient,
                            IngredientAmount, Recipe, Tag)
from users.forms import IngredientAmountFormset


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'hexcolor', 'slug')
    list_editable = ('name', 'hexcolor', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_editable = ('name', 'measurement_unit')
    search_fields = ('name', )
    list_filter = ('measurement_unit', )


class IngredientAmountInLine(admin.TabularInline):
    model = IngredientAmount
    formset = IngredientAmountFormset
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientAmountInLine,)
    list_display = ('pk', 'author', 'name',
                    'cooking_time', 'pub_date', 'followers', 'image')
    list_editable = ('author', 'name')
    list_filter = ('author', 'tags')

    def followers(self, obj):
        return obj.followers.count()
    followers.short_description = 'Количество подписчиков'


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredient', 'recipe', 'amount')
    list_editable = ('ingredient', 'recipe', 'amount')
    list_filter = ('ingredient', )


class FollowOnUserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_editable = ('user', 'author')
    list_filter = ('user', 'author')


class FollowOnRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')
    list_filter = ('user', 'recipe')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(FollowOnUser, FollowOnUserAdmin)
admin.site.register(FollowOnRecipe, FollowOnRecipeAdmin)
