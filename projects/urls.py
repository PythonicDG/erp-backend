from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, DashboardViewSet, CustomerMasterViewSet, StandardMasterViewSet, InspectionAuthorityMasterViewSet, ECNViewSet, CustomerFeedbackViewSet, ASCNViewSet

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'customers', CustomerMasterViewSet, basename='customer')
router.register(r'standards', StandardMasterViewSet, basename='standard')
router.register(r'inspection-authorities', InspectionAuthorityMasterViewSet, basename='inspection-authority')
router.register(r'ecns', ECNViewSet, basename='ecn')
router.register(r'ascns', ASCNViewSet, basename='ascn')
router.register(r'feedbacks', CustomerFeedbackViewSet, basename='feedback')
router.register(r'', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]
