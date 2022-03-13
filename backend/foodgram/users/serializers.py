from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from recipes.models import FollowOnRecipe, FollowOnUser, Recipe
from users.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

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
    is_subscribed = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_is_subscribed')
    recipes_count = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes_count')
    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')

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
            recipe_id = self.context['view'].kwargs.get('id')
            recipe = get_object_or_404(Recipe, id=recipe_id)

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
        FollowOnRecipe.create(user=user, recipe=recipe_id)
        return recipe
