from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from recipes.models import (FollowOnRecipe, Ingredient, IngredientAmount,
                            Recipe, ShopList, Tag)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'hexcolor', 'slug')
        read_only_fields = ('id', )


class IngredientReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', )


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class IngredientAmountSerializer(serializers.ModelSerializer):
    name = serializers.EmailField()
    measurement_unit = serializers.EmailField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount', )


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(read_only=True, many=True)
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
            return FollowOnRecipe.objects.filter(recipe=obj, user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShopList.objects.filter(recipe=obj, user=user).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients_data = self.initial_data.pop('ingredients')

        if not ingredients_data:
            raise ValidationError('Добавьте минимум 1 ингредиент')

        ingredients_list = []
        for ingredient in ingredients_data:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Укажите значение "amount" больше 0'
                )
            ingredient_obj = get_object_or_404(Ingredient,
                                               id=ingredient['id'])
            if ingredient_obj in ingredients_list:
                raise serializers.ValidationError(
                    'Несколько одинаковых ингредиентов. Не повторяйтесь :)'
                )
            ingredients_list.append(ingredient_obj)

        data['ingredients'] = ingredients_data
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients_data:
            id, amount = ingredient['id'], ingredient['amount']
            ingredient_to_add = get_object_or_404(Ingredient, id=id)
            IngredientAmount.objects.create(
                ingredient=ingredient_to_add,
                recipe=recipe, amount=amount
            )
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        IngredientAmount.objects.filter(recipe=instance).all().delete()

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)

        instance.tags.clear()
        instance.tags.set(tags_data)

        for ingredient in ingredients_data:
            id, amount = ingredient['id'], ingredient['amount']
            ingredient_to_add = get_object_or_404(Ingredient, id=id)
            IngredientAmount.objects.create(
                ingredient=ingredient_to_add,
                recipe=instance, amount=amount
            )

        instance.save()
        return instance


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
                raise ValidationError('Вы уже добавили его в список покупок')

        if request.method == 'DELETE':
            if not ShopList.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                raise ValidationError('Рецепт не в списке покупок')
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
