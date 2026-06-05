from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserRole, Notification
from .system_models import SystemConfiguration, CompanyProfile, AuditLog


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email', '').strip()
        if '@' in username_or_email:
            username_or_email = username_or_email.lower()
        password = attrs.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError('Both username/email and password are required.')

        user = authenticate(
            request=self.context.get('request'),
            username=username_or_email,
            password=password
        )

        if not user:
            raise serializers.ValidationError('Invalid username/email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id',
            'employee_id',
            'first_name',
            'last_name',
            'full_name',
            'username',
            'email',
            'phone',
            'department',
            'role',
            'is_active',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']

class TeamMemberSerializer(serializers.ModelSerializer):
    """Detailed serializer for administrative team management."""
    full_name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'employee_id',
            'first_name',
            'last_name',
            'full_name',
            'username',
            'email',
            'phone',
            'department',
            'role',
            'is_active',
            'remarks',
            'password',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password', 'ERP12345') # Default temp password
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration (admin use)."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'password',
            'confirm_password',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'



class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_role = serializers.ReadOnlyField(source='user.role')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_name', 'user_role', 'action', 'target', 
            'module', 'timestamp', 'status'
        ]
        read_only_fields = ['id', 'timestamp']

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.full_name')
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'sender_name', 'title', 
            'message', 'notification_type', 'link', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
