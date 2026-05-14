from django.db import models

class UserRole(models.TextChoices):
    """Enumeration of user roles in the ERP system."""
    ADMIN = 'ADMIN', 'Admin'
    SUPERVISOR = 'SUPERVISOR', 'Supervisor'
    EMPLOYEE = 'EMPLOYEE', 'Employee'
