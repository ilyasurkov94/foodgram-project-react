from turtle import pd
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from recipes.models import Recipe, Tag, Ingredient, FollowOnRecipe
from recipes.models import ShopList, IngredientAmount
from .serializers import TagSerializer, IngredientReadSerializer
from .serializers import RecipeFavoriteSerializer
from .serializers import RecipeReadSerializer, RecipeCreateSerializer
from .permissions import IsAdminOrReadOnly, IsAdminAuthorOrReadPermission
from .pagination import CustomPageSizePagination
from .filters import IsFavoritedFilter, IsInShoppingCartFilter
from .filters import AuthorIdFilter, TagsSlugFilter

from django.http.response import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (IsAdminOrReadOnly, )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadPermission, )
    pagination_class = CustomPageSizePagination
    filter_backends = (IsFavoritedFilter, IsInShoppingCartFilter,
                       AuthorIdFilter, TagsSlugFilter)
    filterset_fields = ('is_favorited', 'is_in_shopping_cart',
                        'author', 'tags')

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def destroy(self, request, pk=None):
        user = self.request.user
        obj = self.get_object()
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if user.is_admin or obj.author == user:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)

    """
    Определили действия для api/recipes/{id}/favorite
    """
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        is_already_follow = FollowOnRecipe.objects.filter(user=user,
                                                          recipe=recipe)
        if request.method == 'POST':
            if not is_already_follow:
                FollowOnRecipe.objects.create(user=user, recipe=recipe)
                serializer = RecipeFavoriteSerializer(
                    recipe, context={'request': request}
                )
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED
                                )
            else:
                return Response('Error: Вы уже подписаны на рецепт '
                                f'{recipe.name} (id - {pk})',
                                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if is_already_follow:
                following_recipe = get_object_or_404(
                    FollowOnRecipe,
                    user=user,
                    recipe=recipe
                )
                following_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response('Error: Вы не были подписаны на рецепт '
                                f'{recipe.name} (id - {pk})',
                                status=status.HTTP_400_BAD_REQUEST)

    """
    Определили действия при api/recipes/{id}/shopping_cart
    """
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        in_shoplist = ShopList.objects.filter(
            user=user, recipe=recipe).exists()

        if request.method == 'POST':
            """Если он уже есть в списке покупок"""
            if not in_shoplist:
                ShopList.objects.create(user=user, recipe=recipe)
                serializer = RecipeFavoriteSerializer(
                    recipe, context={'request': request})
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            else:
                return Response('Error: Вы уже добавили рецепт '
                                f'{recipe.name} (id - {pk}) в список покупок',
                                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            """Если репепта нет в списке покупок"""
            if in_shoplist:
                ShopList.objects.filter(user=user, recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(f'Error: Рецепта {recipe.name} (id - {pk}) '
                                'нет в список покупок',
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    """
    Определили действия при api/recipes/download_shopping_cart/
    """
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request, pk=None):
        user = request.user
        shop_list_data = IngredientAmount.objects.filter(
            recipe__users_shoplist__user=user)

        shoplist_to_download = {}
        for item in shop_list_data:
            ingredient_name = item.ingredient.name
            measurement = item.ingredient.measurement_unit
            amount = item.amount

            if ingredient_name not in shoplist_to_download:
                shoplist_to_download[ingredient_name] = {
                    'measurement': measurement,
                    'amount': amount
                }
            else:
                shoplist_to_download[ingredient_name]['amount'] += amount

        file_name = f'Список покупок. Автор {user.first_name} {user.last_name}'
        doc_title = f'Список покупок. Автор {user.first_name} {user.last_name}'
        title = (f'Список покупок. Автор {user.first_name} {user.last_name}')
        response = HttpResponse(content_type='application/pdf')
        content_disposition = f'attachment; filename="{file_name}.pdf"'
        response['Content-Disposition'] = content_disposition
        pdf = canvas.Canvas(response)
        pdf.setTitle(doc_title)
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdf.setFont('DejaVuSans', 24)
        pdf.drawCentredString(300, 770, title)
        pdf.line(30, 710, 565, 710)
        string_height = 670

        for name, info in shoplist_to_download.items():
            pdf.drawString(
                40,
                string_height,
                f'{name} - {info["amount"]}{info["measurement"]}'
            )
            string_height -= 50
        pdf.showPage()
        pdf.save()
        return response
