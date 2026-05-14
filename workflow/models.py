from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from projects.models import Project

class StageTemplate(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    assigned_role = models.CharField(
        max_length=20, 
        choices=[('ADMIN', 'Admin'), ('SUPERVISOR', 'Supervisor'), ('EMPLOYEE', 'Employee')],
        default='EMPLOYEE'
    )
    approval_required = models.BooleanField(default=True)
    allow_attachments = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_stage_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = _("Stage Template")
        verbose_name_plural = _("Stage Templates")

    def __str__(self):
        return self.name

class FormField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('dropdown', 'Dropdown'),
        ('multi_select', 'Multi Select'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio Button'),
        ('date', 'Date Picker'),
        ('file', 'File Upload'),
        ('grid', 'Table/Grid Input'),
        ('boolean', 'Boolean Switch'),
    ]

    stage_template = models.ForeignKey(StageTemplate, on_delete=models.CASCADE, related_name='fields')
    section = models.CharField(max_length=100, blank=True, null=True, help_text="Grouping name to divide the form into sections")
    label = models.CharField(max_length=255)
    name = models.CharField(max_length=100) 
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    default_value = models.CharField(max_length=255, blank=True, null=True)
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    is_readonly = models.BooleanField(default=False)
    order = models.PositiveIntegerField()
    options = models.JSONField(default=list, blank=True, help_text="For dropdowns, radio, multi-select")
    configuration = models.JSONField(default=dict, blank=True, help_text="For grid/table: {'columns': [], 'rows': []}")

    class Meta:
        ordering = ['order']
        unique_together = ['stage_template', 'name']

    def __str__(self):
        return f"{self.stage_template.name} - {self.label}"

class StageInstance(models.Model):
    class Status(models.TextChoices):
        LOCKED = 'Locked', _('Locked')
        UNLOCKED = 'Unlocked', _('Unlocked')
        IN_PROGRESS = 'In Progress', _('In Progress')
        SUBMITTED = 'Submitted', _('Submitted')
        PENDING_APPROVAL = 'Pending Approval', _('Pending Approval')
        UNDER_REVIEW = 'Under Review', _('Under Review')
        APPROVED = 'Approved', _('Approved')
        REJECTED = 'Rejected', _('Rejected')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='workflow_stages')
    template = models.ForeignKey(StageTemplate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LOCKED)
    order = models.PositiveIntegerField()
    
    unlocked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['project', 'template']

    def __str__(self):
        return f"{self.project.pid} - {self.template.name} ({self.status})"

class StageSubmission(models.Model):
    class SubmissionStatus(models.TextChoices):
        DRAFT = 'Draft', _('Draft')
        SUBMITTED = 'Submitted', _('Submitted')
        UNDER_REVIEW = 'Under Review', _('Under Review')
        APPROVED = 'Approved', _('Approved')
        REJECTED = 'Rejected', _('Rejected')

    stage_instance = models.ForeignKey(StageInstance, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.DRAFT)
    remarks = models.TextField(blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Submission for {self.stage_instance} by {self.submitted_by}"

class StageActivity(models.Model):
    stage_instance = models.ForeignKey(StageInstance, on_delete=models.CASCADE, related_name='activities')
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    remarks = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
