from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, CustomTokenRefreshView, LogoutView, MeView, TeamViewSet

app_name = 'authentication'

router = DefaultRouter()
router.register(r'team', TeamViewSet, basename='team')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
