from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]
