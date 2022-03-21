from django.contrib import admin
from recipes.models import (FollowOnRecipe, FollowOnUser, Ingredient,
                            IngredientAmount, Recipe, Tag)
from users.forms import IngredientAmountFormset


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')


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
    search_fields = ('author__username', 'author__email', 'name')
    list_filter = ('tags', )

    def followers(self, obj):
        return obj.followers.count()
    followers.short_description = 'Количество подписчиков'


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredient', 'recipe',
                    'amount', 'username', 'email')
    list_editable = ('ingredient', 'recipe', 'amount')
    search_fields = ('recipe__name', 'recipe__author__username',
                     'recipe__author__email')

    def username(self, obj):
        return obj.recipe.author.username

    def email(self, obj):
        return obj.recipe.author.email


class FollowOnUserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_editable = ('user', 'author')
    search_fields = ('user', 'user__email')


class FollowOnRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')
    search_fields = ('user', 'user__email')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(FollowOnUser, FollowOnUserAdmin)
admin.site.register(FollowOnRecipe, FollowOnRecipeAdmin)
