from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class ProjectStatus(models.TextChoices):
    DRAFT = 'Draft', _('Draft')
    OPEN = 'Open', _('Open')
    IN_PROGRESS = 'In Progress', _('In Progress')
    CLOSED = 'Closed', _('Closed')
    REJECTED = 'Rejected', _('Rejected')
    UNDER_REVIEW = 'Under Review', _('Under Review')
    PENDING_APPROVAL = 'Pending Approval', _('Pending Approval')

class CustomerMaster(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Customer Name"))
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Customer Category"))
    mobile_number = models.CharField(max_length=20, verbose_name=_("Mobile Number"))
    alternate_mobile_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Alternate Mobile Number"))
    email = models.EmailField(verbose_name=_("Email"))
    remarks = models.TextField(blank=True, null=True, verbose_name=_("Remark/Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Customer Master")
        verbose_name_plural = _("Customer Masters")

    def __str__(self):
        return self.name

class Project(models.Model):
    pid = models.CharField(max_length=20, unique=True, blank=True, verbose_name=_("Project ID"))
    name = models.CharField(max_length=255, verbose_name=_("Project Name"))
    customer = models.ForeignKey(
        CustomerMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name=_("Customer")
    )
    # Keeping for backward compatibility if needed, or removing
    customer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Customer Name String"))
    customer_part_no = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Customer Part No"))
    pcepl_part_no = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("PCEPL Part No"))
    project_type = models.CharField(max_length=100, verbose_name=_("Project Type"))
    inspection_authority = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Inspection Authority"))
    applicable_standard = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Applicable Standard"))
    
    date_received = models.DateField(verbose_name=_("Date Received"))
    month_received = models.CharField(max_length=50, blank=True, verbose_name=_("Month Received")) # e.g., "March 2025"
    target_completion_date = models.DateField(blank=True, null=True, verbose_name=_("Target Completion Date"))
    
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
        verbose_name=_("Project Status")
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='supervised_projects'
    )
    assigned_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __str__(self):
        return f"{self.pid} - {self.name}"

    def save(self, *args, **kwargs):
        from .services import ProjectService
        if not self.pid:
            self.pid = ProjectService.generate_pid(self.date_received)
        if not self.month_received:
            self.month_received = ProjectService.get_month_received_string(self.date_received)
        super().save(*args, **kwargs)
