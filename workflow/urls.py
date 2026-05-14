from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StageTemplateViewSet, StageInstanceViewSet

router = DefaultRouter()
router.register(r'templates', StageTemplateViewSet, basename='stage-template')
router.register(r'instances', StageInstanceViewSet, basename='stage-instance')

urlpatterns = [
    path('', include(router.urls)),
]
