from django.forms import ValidationError
from .models import User
from django.shortcuts import get_object_or_404
from recipes.models import FollowOnUser, Recipe, FollowOnRecipe
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'password')
        read_only_fields = ('id, is_subscribed',)
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return FollowOnUser.objects.filter(
                user=user, author=obj.id).exists()
        return False


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class FollowOnUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email')
    id = serializers.EmailField(source='author.id')
    username = serializers.EmailField(source='author.username')
    first_name = serializers.EmailField(source='author.first_name')
    last_name = serializers.EmailField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FollowOnUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return FollowOnUser.objects.filter(
                user=user, author=obj.author
            ).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = self.context['recipes_limit']
        if recipes_limit:
            recipes = obj.author.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.author.recipes.all()
        return FollowOnRecipeSerializer(recipes, many=True).data


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowOnUser
        fields = ('user', 'author')

    def validate(self, obj):
        user = obj['user']
        author = obj['author']
        request_method = self.context.get('request').method
        subscribed = FollowOnUser.objects.filter(
            user=user, author=author).exists()

        if subscribed and request_method == 'POST':
            raise ValidationError('Вы уже подписаны на автора')
        if not subscribed and request_method == 'DELETE':
            raise ValidationError('Вы не были подписаны на автора')
        if user == author:
            raise ValidationError('Вы указали свой id')

        return obj


class FollowOnRecipeSerializer(serializers.ModelSerializer):
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

            """Проверили наличие в в избранном"""
            if FollowOnRecipe.objects.filter(user=request.user,
                                             recipe=recipe).exists():
                raise ValidationError('Вы уже добавили его в избранное')

        if request.method == 'DELETE':
            if not FollowOnRecipe.objects.filter(user=request.user,
                                                 recipe=recipe).exists():
                raise ValidationError('Рецепт не в списке избранного')

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        """Создали записть в FollowOnRecipe"""
        FollowOnRecipe.create(user=user, recipe=recipe_id)
        return recipe
