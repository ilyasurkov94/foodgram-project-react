from rest_framework import filters
from rest_framework.filters import SearchFilter


class IsFavoritedFilter(filters.BaseFilterBackend):
    """
    Фильтрация по избранным рецептам
    """
    def filter_queryset(self, request, queryset, view):
        is_favorited = request.GET.get('is_favorited')
        user = request.user

        if is_favorited != '1':
            return queryset

        if user.is_authenticated:
            return queryset.filter(followers__user=user)
        return None


class IsInShoppingCartFilter(filters.BaseFilterBackend):
    """
    Фильтрация по рецептам в списке покупок
    """
    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.GET.get('is_in_shopping_cart')
        user = request.user

        if is_in_shopping_cart != '1':
            return queryset

        if user.is_authenticated:
            return queryset.filter(users_shoplist__user=user)
        return None


class AuthorIdFilter(filters.BaseFilterBackend):
    """
    Фильтрация по автору
    """
    def filter_queryset(self, request, queryset, view):
        author = request.GET.get('author')

        if author:
            return queryset.filter(author=author)
        return queryset


class TagsSlugFilter(filters.BaseFilterBackend):
    """
    Фильтрация по имени тега
    """
    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
