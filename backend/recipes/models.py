from django.db import models
from users.models import User
from django.core import validators


class Tag(models.Model):
    name = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='Название тега',
        help_text='Имя тега, не более 50 символов',
        error_messages={
            'unique': ('Такой тег уже есть'),
        },
    )
    color = models.CharField(
        max_length=7,
        default='#ffffff',
        unique=True,
        verbose_name='HEX-цвет',
        help_text='Используйте формат "#fffff"',
        error_messages={
            'unique': ('Такой hex-цвет уже используется'),
        },
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug-адрес',
        help_text='Выберите название-ссылку на тег',
        error_messages={
            'unique': ('Такой slug уже используется'),
        },
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=500,
        verbose_name='Название ингредиента',
        help_text='Выберите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=500,
        verbose_name='Единица измерения',
        help_text='Укажите единицу измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        help_text='Выбери автора рецепта'
    )
    name = models.CharField(
        max_length=500,
        verbose_name='Название рецепта',
        help_text='Укажи название рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Опишите рецепт'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='IngredientAmount',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время готовки, мин.'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
    )

    class Meta:
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Рецепты',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Ингредиенты',
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=(
            validators.MinValueValidator(
                1, message='Минимальный показатель - 1'),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ['-id']
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='ingredient_recipe_relations'),
        )

    def __str__(self):
        return f'{self.ingredient.name} in {self.recipe.name}'


class FollowOnUser(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        help_text='Кто подписан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text='На какого автора подписан')

    class Meta:
        verbose_name = 'Подписка юзера на автора'
        verbose_name_plural = 'Подписки юзера на автора'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='user_author_relations'),
        )

    def __str__(self):
        return f'{self.user.username} follows {self.author.username}'


class FollowOnRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_recipe',
        help_text='Кто подписан'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text='На какой рецепт подписан'
    )

    class Meta:
        verbose_name = 'Подписка юзера на рецепт'
        verbose_name_plural = 'Подписки юзера на рецепт'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_recipe_relations'),
        )

    def __str__(self):
        return f'{self.user.username} follows {self.recipe.name}'


class ShopList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoplist',
        help_text='В списке покупок'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_shoplist',
        help_text='У кого в списке покупок'
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_recipe_shoplist_relations'),
        )

    def __str__(self):
        return f'{self.user.username} follows {self.recipe.name}'
