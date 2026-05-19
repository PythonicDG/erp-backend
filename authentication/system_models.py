from django.db import models
from django.utils.translation import gettext_lazy as _
from .choices import UserRole

class SystemConfiguration(models.Model):
    company_name = models.CharField(max_length=255, default="PCEPL ERP System")
    financial_year = models.CharField(max_length=50, default="2024-2025")
    system_version = models.CharField(max_length=20, default="v1.0.4-stable")
    last_update = models.DateTimeField(auto_now=True)
    server_info = models.CharField(max_length=255, default="Production Node 01 - Windows Server")
    
    # Singleton pattern
    def save(self, *args, **kwargs):
        if not self.pk and SystemConfiguration.objects.exists():
            return
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("System Configuration")
        verbose_name_plural = _("System Configuration")

    def __str__(self):
        return f"{self.company_name} Settings"

class CompanyProfile(models.Model):
    name = models.CharField(max_length=255, default="PCEPL Engineering")
    email = models.EmailField(default="admin@pcepl.com")
    phone = models.CharField(max_length=20, default="+91 20 2445 1234")
    website = models.URLField(default="https://www.pcepl-engineering.com")
    address = models.TextField(default="Plot No. 45, Sector 12, PCMC Industrial Area")
    city = models.CharField(max_length=100, default="Pune")
    state = models.CharField(max_length=100, default="Maharashtra")
    postal_code = models.CharField(max_length=20, default="411018")
    country = models.CharField(max_length=100, default="India")
    logo = models.ImageField(upload_to='', null=True, blank=True)
    audit_logs_enabled = models.BooleanField(default=True)
    watermark_under_approval = models.CharField(max_length=255, default="UNDER APPROVAL")
    watermark_released = models.CharField(max_length=255, default="RELEASED")
    
    class Meta:
        verbose_name = _("Company Profile")
        verbose_name_plural = _("Company Profile")

    def save(self, *args, **kwargs):
        if not self.pk and CompanyProfile.objects.exists():
            return
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    user = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    module = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SUCCESS')

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} ({self.timestamp})"
