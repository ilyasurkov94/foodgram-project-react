from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from recipes.models import (FollowOnRecipe, Ingredient, IngredientAmount,
                            Recipe, ShopList, Tag)
from api.filters import (AuthorIdFilter, IsFavoritedFilter,
                         IsInShoppingCartFilter, TagsSlugFilter,
                         IngredientSearchFilter)
from api.pagination import CustomPageSizePagination
from api.permissions import IsAdminAuthorOrReadPost, IsAdminOrReadOnly
from api.serializers import (IngredientReadSerializer, RecipeCreateSerializer,
                             RecipeFavoriteSerializer, RecipeReadSerializer,
                             TagSerializer)
from django.db.models import Sum


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (IsAdminOrReadOnly, )
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadPost, )
    pagination_class = CustomPageSizePagination
    filter_backends = (IsFavoritedFilter, IsInShoppingCartFilter,
                       AuthorIdFilter, TagsSlugFilter)
    filterset_fields = ('is_favorited', 'is_in_shopping_cart',
                        'author', 'tags')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def destroy(self, request, pk=None):
        user = self.request.user
        obj = self.get_object()
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if user.is_admin or obj.author == user:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated, ))
    def favorite(self, request, pk):
        """
        Определили действия для api/recipes/{id}/favorite
        """
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        is_already_follow = FollowOnRecipe.objects.filter(user=user,
                                                          recipe=recipe)
        if request.method == 'POST':
            if is_already_follow:
                return Response('Error: Вы уже подписаны на рецепт '
                                f'{recipe.name} (id - {pk})',
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                FollowOnRecipe.objects.create(user=user, recipe=recipe)
                serializer = RecipeFavoriteSerializer(
                    recipe, context={'request': request}
                )
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED
                                )

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

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """
        Определили действия при api/recipes/{id}/shopping_cart
        """
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        in_shoplist = ShopList.objects.filter(
            user=user, recipe=recipe).exists()

        if request.method == 'POST':
            if in_shoplist:
                return Response('Error: Вы уже добавили рецепт '
                                f'{recipe.name} (id - {pk}) в список покупок',
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                ShopList.objects.create(user=user, recipe=recipe)
                serializer = RecipeFavoriteSerializer(
                    recipe, context={'request': request})
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if in_shoplist:
                ShopList.objects.filter(user=user, recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(f'Error: Рецепта {recipe.name} (id - {pk}) '
                                'нет в список покупок',
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class DownloadShopGetView(APIView):
    def get(self, request):
        PDF = 'application/pdf'
        user = request.user
        if user.is_anonymous:
            return Response('Вы не авторизованы',
                            status=status.HTTP_401_UNAUTHORIZED)
        shoplist_to_download = IngredientAmount.objects.filter(
            recipe__users_shoplist__user=user).values(
                'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(count=Sum('amount'))

        file_name = f'Список покупок. Автор {user.first_name} {user.last_name}'
        doc_title = f'Список покупок. Автор {user.first_name} {user.last_name}'
        title = (f'Список покупок. Автор {user.first_name} {user.last_name}')
        response = HttpResponse(content_type=PDF)
        content_disposition = f'attachment; filename="{file_name}.pdf"'
        response['Content-Disposition'] = content_disposition
        pdf = canvas.Canvas(response)
        pdf.setTitle(doc_title)
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdf.setFont('DejaVuSans', 24)
        pdf.drawCentredString(300, 770, title)
        pdf.line(30, 710, 565, 710)
        string_height = 650

        for item in shoplist_to_download:
            name = item["ingredient__name"].capitalize()
            count = item["count"]
            measurement_unit = item["ingredient__measurement_unit"]
            pdf.drawString(
                40,
                string_height,
                (f'{name} - '
                 f'{count} '
                 f'{measurement_unit}'
                 )
            )
            string_height -= 50

        pdf.showPage()
        pdf.save()
        return response
