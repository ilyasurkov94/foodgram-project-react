from django.forms import ValidationError
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.shortcuts import get_object_or_404
from users.serializers import CustomUserSerializer
from recipes.models import Tag, Ingredient, Recipe
from recipes.models import IngredientAmount
from recipes.models import ShopList, FollowOnRecipe
from rest_framework.response import Response
from rest_framework import status


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
    # id = serializers.ReadOnlyField(source='ingredient.id')
    # name = serializers.ReadOnlyField(source='ingredient.name')
    # measurement_unit = serializers.ReadOnlyField(
    #     source='ingredient.measurement_unit'
    # )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount', )  # ? id


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
        """Вытащили ингредиенты"""
        ingredients_data = self.initial_data.pop('ingredients')

        """Проверка наличия ингредиентов"""
        if not ingredients_data:
            raise ValidationError('Добавьте минимум 1 ингредиент')

        """Проверка отсутствия повторений и amount > 0"""
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
        """Вытащили ингредиенты"""
        ingredients_data = validated_data.pop('ingredients')

        """Вытащили теги"""
        tags_data = validated_data.pop('tags')

        """Создали рецепт"""
        recipe = Recipe.objects.create(**validated_data)

        """Создали связь ингредиентов и рецепта"""
        for ingredient in ingredients_data:
            id, amount = ingredient['id'], ingredient['amount']
            ingredient_to_add = get_object_or_404(Ingredient, id=id)
            IngredientAmount.objects.create(
                ingredient=ingredient_to_add,
                recipe=recipe, amount=amount
            )
        """Добавили теги к рецепту"""
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        """Удалили все связи с рецептом"""
        IngredientAmount.objects.filter(recipe=instance).all().delete()

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)

        """Обновили теги"""
        instance.tags.clear()
        instance.tags.set(tags_data)

        """Создали связь ингредиентов и рецепта"""
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
            """Взяли id из url"""
            recipe_id = self.context['view'].kwargs.get('id')

            """Проверили наличие такого рецепта"""
            recipe = get_object_or_404(Recipe, id=recipe_id)

            """Проверили наличие в списке покупок"""
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
        """Создали записть в ShopList"""
        shop_list = ShopList.create(user=user, recipe=recipe_id)
        return recipe


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    # image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
