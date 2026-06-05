from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, CustomTokenRefreshView, LogoutView, MeView, TeamViewSet,
    CompanyProfileView, AuditLogViewSet, NotificationViewSet,
    DatabaseBackupView, DatabaseRestoreView, DatabaseResetView
)

app_name = 'authentication'

router = DefaultRouter()
router.register(r'team', TeamViewSet, basename='team')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-logs')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('company-profile/', CompanyProfileView.as_view(), name='company-profile'),
    path('database/backup/', DatabaseBackupView.as_view(), name='database-backup'),
    path('database/restore/', DatabaseRestoreView.as_view(), name='database-restore'),
    path('database/reset/', DatabaseResetView.as_view(), name='database-reset'),
    path('', include(router.urls)),
]
