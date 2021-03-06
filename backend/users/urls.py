from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, SubscriptionsViewSet

app_name = 'users'

router = DefaultRouter()

router.register(r'users/subscriptions',
                SubscriptionsViewSet,
                basename='subscriptions')
router.register(r'users',
                UserViewSet,
                basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
