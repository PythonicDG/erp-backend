from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, Notification
from .system_models import SystemConfiguration, CompanyProfile, AuditLog
from .serializers import (
    LoginSerializer, UserSerializer, TeamMemberSerializer,
    CompanyProfileSerializer, AuditLogSerializer, NotificationSerializer
)

from .mixins import AuditLogMixin
from .permissions import IsAdmin, IsAdminOrSupervisor, IsSuperAdmin

class TeamViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing team members (Admins and Supervisors).
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = TeamMemberSerializer
    filterset_fields = ['role', 'is_active', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    audit_module = "Team"

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSupervisor()]

    def get_audit_target(self, instance):
        return f"{instance.full_name} ({instance.employee_id})"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.role == 'SUPERADMIN':
            return Response(
                {"detail": "SuperAdmin accounts can only be deleted through the Django admin panel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class LoginView(GenericAPIView):
    """
    POST /api/auth/login/
    Authenticate user with email and password, returns JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary='User Login',
        description='Authenticate with email and password to receive JWT access and refresh tokens.',
        responses={
            200: OpenApiResponse(description='Login successful'),
            400: OpenApiResponse(description='Invalid credentials'),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': serializer.errors.get('non_field_errors', ['Invalid credentials'])[0]
                    if 'non_field_errors' in serializer.errors
                    else 'Validation failed',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # Add custom claims to the token
        refresh['role'] = user.role
        refresh['email'] = user.email
        refresh['full_name'] = user.full_name

        user_data = UserSerializer(user).data

        return Response(
            {
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user': user_data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Refresh the access token using a valid refresh token.
    """

    @extend_schema(
        summary='Refresh Token',
        description='Submit a valid refresh token to receive a new access token.',
        responses={
            200: OpenApiResponse(description='Token refreshed successfully'),
            401: OpenApiResponse(description='Invalid or expired refresh token'),
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response(
                {
                    'success': True,
                    'message': 'Token refreshed successfully',
                    'data': {
                        'access': response.data.get('access'),
                    },
                },
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {
                    'success': False,
                    'message': 'Invalid or expired refresh token',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(GenericAPIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token to log the user out.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='User Logout',
        description='Blacklist the refresh token to invalidate the session.',
        responses={
            200: OpenApiResponse(description='Logout successful'),
            400: OpenApiResponse(description='Invalid refresh token'),
        },
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {
                    'success': False,
                    'message': 'Refresh token is required',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {
                    'success': True,
                    'message': 'Logout successful',
                },
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {
                    'success': False,
                    'message': 'Invalid refresh token',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(GenericAPIView):
    """
    GET /api/auth/me/
    Returns the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        summary='Current User Profile',
        description='Returns the authenticated user profile data.',
        responses={
            200: OpenApiResponse(description='User profile retrieved'),
            401: OpenApiResponse(description='Not authenticated'),
        },
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(
            {
                'success': True,
                'message': 'User profile retrieved successfully',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CompanyProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyProfileSerializer

    def get(self, request):
        profile = CompanyProfile.objects.first()
        if not profile:
            profile = CompanyProfile.objects.create(name="PCEPL Engineering")
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        profile = CompanyProfile.objects.first()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            from .utils import log_action
            log_action(
                user=request.user,
                action="UPDATE",
                target="Company Profile",
                module="Settings"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['module', 'status']
    search_fields = ['user_name', 'action', 'target', 'module']

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'count': count})


import io
import tempfile
from django.db import transaction
from django.core.management import call_command
from django.http import HttpResponse

class DatabaseBackupView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        buffer = io.StringIO()
        call_command(
            'dumpdata', 
            exclude=['contenttypes', 'auth.Permission', 'sessions', 'admin.logentry'], 
            stdout=buffer
        )
        backup_data = buffer.getvalue()
        
        response = HttpResponse(backup_data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="erp_backup.json"'
        
        from .utils import log_action
        log_action(
            user=request.user,
            action="BACKUP",
            target="Database",
            module="Settings"
        )
        return response


class DatabaseRestoreView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not file_obj.name.endswith('.json'):
            return Response({"error": "Only JSON backup files are supported"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            with transaction.atomic():
                call_command('loaddata', temp_file_path)

            from .utils import log_action
            log_action(
                user=request.user,
                action="RESTORE",
                target="Database",
                module="Settings"
            )
            return Response({"success": True, "message": "Database restored successfully"})
        except Exception as e:
            return Response({"error": f"Failed to restore database: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseResetView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        try:
            with transaction.atomic():
                from projects.models import Project, CustomerMaster, StandardMaster, InspectionAuthorityMaster
                from .models import User, Notification
                from .system_models import AuditLog
                
                # Delete all projects (cascades to ECNs, ASCNs, Feedbacks, StageInstances, submissions, etc.)
                Project.objects.all().delete()
                
                # Delete all customers
                CustomerMaster.objects.all().delete()
                
                # Delete all standards
                StandardMaster.objects.all().delete()
                
                # Delete all inspection authorities
                InspectionAuthorityMaster.objects.all().delete()
                
                # Delete all users except SuperAdmins
                User.objects.exclude(role='SUPERADMIN').delete()
                
                # Delete all audit logs
                AuditLog.objects.all().delete()
                
                # Delete all notifications
                Notification.objects.all().delete()
                
                from .utils import log_action
                log_action(
                    user=request.user,
                    action="RESET",
                    target="Database",
                    module="Settings"
                )
            
            return Response({"success": True, "message": "All operational data, users (excluding SuperAdmins), standards, and inspection authorities have been reset successfully."})
        except Exception as e:
            return Response({"error": f"Reset failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


