from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from recipes.models import (FollowOnRecipe, Ingredient, IngredientAmount,
                            Recipe, ShopList, Tag)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', )


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient'
                                                 '.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        read_only=True,
        many=True,
        source='ingredient_amounts')
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return FollowOnRecipe.objects.filter(
                recipe=obj, user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShopList.objects.filter(recipe=obj, user=user).exists()
        return False


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(
        many=True,
        read_only=True,
        source='ingredient_amounts')
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')
        if not ingredients_data:
            raise serializers.ValidationError('Добавьте минимум 1 ингредиент')

        ingredients_unique_list = []
        for ingredient in ingredients_data:
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    'Укажите значение "amount" больше 0'
                )
            ingredient_to_check = get_object_or_404(Ingredient,
                                                    id=ingredient['id']
                                                    )
            if ingredient_to_check in ingredients_unique_list:
                raise serializers.ValidationError(
                    'Несколько одинаковых ингредиентов. Не повторяйтесь')
            ingredients_unique_list.append(ingredient_to_check)

        data['ingredients'] = ingredients_data

        return data

    def create(self, validated_data):
        author = self.context['request'].user
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author,
                                       image=image,
                                       **validated_data)
        tags = self.initial_data.get('tags')
        recipe.tags.set(tags)

        for ingredient in ingredients_data:
            id = ingredient.get('id')
            amount = int(ingredient.get('amount'))
            IngredientAmount.objects.create(
                ingredient_id=id,
                recipe=recipe,
                amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()

        ingredients_data = validated_data.pop('ingredients')
        tags = self.initial_data.get('tags')
        for tag in tags:
            instance.tags.add(tag)

        for ingredient in ingredients_data:
            ingredient_id = ingredient.get('id')
            ingredient_amount = ingredient.get('amount')
            IngredientAmount.objects.create(
                recipe=instance,
                ingredient_id=ingredient_id,
                amount=ingredient_amount
            )
        return super().update(instance, validated_data)


class ShopListCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        request = self.context['request']
        if request.method == 'POST':
            recipe_id = self.context['view'].kwargs.get('id')

            recipe = get_object_or_404(Recipe, id=recipe_id)

            if ShopList.objects.filter(user=request.user,
                                       recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Вы уже добавили его в список покупок'
                )

        if request.method == 'DELETE':
            if not ShopList.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Рецепт не был в списке покупок'
                )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShopList.create(user=user, recipe=recipe_id)
        return recipe


class RecipeFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
