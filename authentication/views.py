from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import LoginSerializer, UserSerializer


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
