import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from authentication.models import User, UserRole


def create_test_users():
    """Create sample users for each role for development/testing."""

    users = [
        {
            'email': 'admin@erp.com',
            'first_name': 'System',
            'last_name': 'Admin',
            'phone': '+91-9876543210',
            'role': UserRole.ADMIN,
            'password': 'admin@123',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'email': 'supervisor@erp.com',
            'first_name': 'Project',
            'last_name': 'Supervisor',
            'phone': '+91-9876543211',
            'role': UserRole.SUPERVISOR,
            'password': 'supervisor@123',
        },
        {
            'email': 'employee@erp.com',
            'first_name': 'Team',
            'last_name': 'Employee',
            'phone': '+91-9876543212',
            'role': UserRole.EMPLOYEE,
            'password': 'employee@123',
        },
    ]

    for user_data in users:
        password = user_data.pop('password')
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults=user_data,
        )
        if created:
            user.set_password(password)
            user.save()
            print(f'✅ Created {user.role} user: {user.email} (password: {password})')
        else:
            print(f'⏭️  User already exists: {user.email}')


if __name__ == '__main__':
    create_test_users()
    print('\n🎉 Test users setup complete!')
