from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (IngredientViewSet, RecipeViewSet, TagsViewSet,
                       DownloadShopGetView)

app_name = 'api'

router = DefaultRouter()
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('recipes/download_shopping_cart/', DownloadShopGetView.as_view(),
         name='download_shopping_cart'),
    path('', include(router.urls)),

]
