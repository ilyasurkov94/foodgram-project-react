from rest_framework import filters


class IsFavoritedFilter(filters.BaseFilterBackend):
    """
    Фильтрация по избранным рецептам
    """
    def filter_queryset(self, request, queryset, view):
        is_favorited = request.GET.get('is_favorited')
        user = request.user
        if user.is_authenticated:
            if is_favorited == '1':
                return queryset.filter(followers__user=user)

        """Если запрос на фильтрацию от анонима, но вернуть None"""
        if is_favorited == '1' and (not user.is_authenticated):
            return None
        return queryset


class IsInShoppingCartFilter(filters.BaseFilterBackend):
    """
    Фильтрация по рецептам в списке покупок
    """
    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.GET.get('is_in_shopping_cart')
        user = request.user

        if user.is_authenticated and is_in_shopping_cart == '1':
            return queryset.filter(users_shoplist__user=user)

        """Если запрос на фильтрацию от анонима, но вернуть None"""
        if is_in_shopping_cart == '1' and (not user.is_authenticated):
            return None
        return queryset


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
