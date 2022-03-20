from django.shortcuts import get_object_or_404
from django_filters import rest_framework
from recipes.models import FollowOnUser
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.pagination import CustomPageSizePagination
from api.permissions import AllowAnyGetPost, CurrentUserOrAdmin
from users.models import User
from users.serializers import (ChangePasswordSerializer, CustomUserSerializer,
                               FollowOnUserSerializer, SubscribeSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAnyGetPost, )
    pagination_class = CustomPageSizePagination

    @action(detail=False, methods=('get', ),
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Опеределили действие при api/users/me
        """
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=('post', ),
            permission_classes=(CurrentUserOrAdmin, ))
    def set_password(self, request, *args, **kwargs):
        """
        Определили действия при api/users/set_password
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        new_password = serializer.data.get("new_password")
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated, ))
    def subscribe(self, request, pk):
        """
        Определили действия при api/users/{id}/subscribe
        """
        author = get_object_or_404(User, id=pk)
        user = self.request.user
        is_already_follow = FollowOnUser.objects.filter(
            user=user, author=author).exists()
        data = {
            'user': user.pk,
            'author': author.pk,
        }
        serializer = SubscribeSerializer(data=data,
                                         context={'request': request}
                                         )
        if request.method == 'POST':
            if not is_already_follow:
                new_following = FollowOnUser.objects.create(
                    user=user,
                    author=author
                )
                recipes_limit = self.request.query_params.get('recipes_limit')
                serializer = FollowOnUserSerializer(
                    new_following,
                    context={'request': request,
                             'recipes_limit': recipes_limit}
                )
                return Response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response('Error: Вы уже подписаны на автора '
                            f'{author.username} (id - {pk})',
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if is_already_follow:
                FollowOnUser.objects.filter(user=user, author=author).delete()
                return Response('Подписка удалена',
                                status=status.HTTP_204_NO_CONTENT)
            return Response('Error: Вы не были подписаны на автора '
                            f'{author.username} (id - {pk})',
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class SubscriptionsViewSet(viewsets.ModelViewSet):
    serializer_class = FollowOnUserSerializer
    pagination_class = CustomPageSizePagination
    filter_backends = (rest_framework.DjangoFilterBackend,)
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        user = self.request.user
        return FollowOnUser.objects.filter(
            user=user).select_related('author')

    def get_serializer_context(self):
        """Передали в сериализатор параметр recipes_limit"""
        recipes_limit = self.request.query_params.get('recipes_limit')
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'recipes_limit': recipes_limit
        }
