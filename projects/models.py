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
    project_complexity = models.CharField(
        max_length=10, 
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], 
        default='Medium', 
        verbose_name=_("Project Complexity")
    )
    planned_start_date = models.DateField(blank=True, null=True, verbose_name=_("Planned Start Date"))
    inspection_authority = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Inspection Authority"))
    inspection_authority_fk = models.ForeignKey(
        'InspectionAuthorityMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name=_("Inspection Authority FK")
    )
    applicable_standard = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Applicable Standard"))
    standard = models.ForeignKey(
        'StandardMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name=_("Standard")
    )
    
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
    priority = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Priority"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
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
        if self.standard:
            self.applicable_standard = self.standard.standard_number
        if self.inspection_authority_fk:
            self.inspection_authority = self.inspection_authority_fk.name
        super().save(*args, **kwargs)
        
        if self.status == 'Closed':
            try:
                from django.utils import timezone
                from datetime import timedelta
                from projects.models import CustomerFeedback
                
                scheduled_date = timezone.now().date() + timedelta(days=365)
                default_performance = [
                    {"sr_no": 1, "parameter": "Panel Performance", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 2, "parameter": "PLC / Control Logic Functionality", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 3, "parameter": "Electrical Safety", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 4, "parameter": "Build Quality", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 5, "parameter": "Ease of Maintenance", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 6, "parameter": "Technical Support Responsiveness", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 7, "parameter": "Overall Satisfaction (Based on Usage)", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                    {"sr_no": 9, "parameter": "Documentation", "excellent": False, "good": False, "average": False, "poor": False, "remarks": ""},
                ]
                
                CustomerFeedback.objects.get_or_create(
                    project=self,
                    defaults={
                        "customer_name": self.customer.name if self.customer else self.customer_name or "",
                        "product_name": self.name,
                        "customer_drawing_no": self.customer_part_no or "",
                        "pcepl_part_no": self.pcepl_part_no or "",
                        "panel_dispatch_date": timezone.now().date(),
                        "feedback_collection_date": scheduled_date,
                        "scheduled_date": scheduled_date,
                        "performance_feedback": default_performance,
                        "status": "Scheduled"
                    }
                )
            except Exception:
                pass
                
        try:
            from workflow.services import WorkflowService
            WorkflowService.recalculate_project_timeline(self)
        except Exception:
            pass


class StandardMaster(models.Model):
    CATEGORY_CHOICES = [
        ('ISO', 'ISO'),
        ('IEC', 'IEC'),
        ('Marine IEC', 'Marine IEC'),
        ('IP', 'IP'),
        ('EMC', 'EMC'),
        ('Defence', 'Defence'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    standard_number = models.CharField(max_length=100, unique=True, verbose_name=_("Standard Number"))
    standard_name = models.CharField(max_length=255, verbose_name=_("Standard Name"))
    revision = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Revision / Edition"))
    release_year = models.IntegerField(blank=True, null=True, verbose_name=_("Release Year"))
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['standard_number']
        verbose_name = _("Standard Master")
        verbose_name_plural = _("Standards Master")

    def __str__(self):
        return f"{self.standard_number} - {self.standard_name}"


class InspectionAuthorityMaster(models.Model):
    CATEGORY_CHOICES = [
        ('Marine', 'Marine'),
        ('Customer', 'Customer'),
        ('QA Agency', 'QA Agency'),
        ('Internal', 'Internal'),
        ('Defence', 'Defence'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    authority_id = models.CharField(max_length=100, unique=True, verbose_name=_("Inspection Authority ID"))
    name = models.CharField(max_length=255, verbose_name=_("Inspection Authority Name"))
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Contact Person"))
    applicable_standard = models.ForeignKey(
        StandardMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspection_authorities',
        verbose_name=_("Applicable Standard / Agency")
    )
    approval_type = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Approval Type"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name=_("Status"))
    remarks = models.TextField(blank=True, null=True, verbose_name=_("Remarks"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['authority_id']
        verbose_name = _("Inspection Authority Master")
        verbose_name_plural = _("Inspection Authorities Master")

    def __str__(self):
        return f"{self.authority_id} - {self.name}"


class ECNStatus(models.TextChoices):
    DRAFT = 'Draft', _('Draft')
    SUBMITTED = 'Submitted', _('Submitted')
    REVIEWED = 'Reviewed', _('Reviewed')
    APPROVED = 'Approved', _('Approved')
    REJECTED = 'Rejected', _('Rejected')


class ECN(models.Model):
    ecn_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name=_("ECN Number"))
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='ecns',
        verbose_name=_("Project")
    )
    raised_department = models.CharField(max_length=255, verbose_name=_("ECN Raised Department"))
    change_initiated_by = models.CharField(max_length=255, verbose_name=_("Change Initiated By"))
    ecn_date = models.DateField(verbose_name=_("ECN Date"))
    old_revision_no = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Old Revision No."))
    old_revision_date = models.DateField(blank=True, null=True, verbose_name=_("Old Revision Date"))
    new_revision = models.CharField(max_length=50, verbose_name=_("New Revision"))
    
    # Section 2: Details of Change (List of dicts: [{'sr_no': 1, 'description': '...', 'reason': '...'}])
    details_of_change = models.JSONField(default=list, blank=True, verbose_name=_("Details of Change"))
    
    # Section 3: Impact Analysis (List of dicts: [{'name': '...', 'selection': 'Yes/No', 'remarks': '...'}])
    impact_analysis = models.JSONField(default=list, blank=True, verbose_name=_("Impact Analysis"))
    
    # Section 4: Action Plan (List of dicts: [{'action': '...', 'responsible': '...', 'target_date': 'YYYY-MM-DD', 'remark': '...'}])
    action_plan = models.JSONField(default=list, blank=True, verbose_name=_("Action Plan"))
    attachments = models.JSONField(default=list, blank=True, verbose_name=_("Attachments"))
    
    # Section 5: Approvals
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ecns_initiated',
        verbose_name=_("Initiator")
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ecns_reviewed',
        verbose_name=_("Reviewed By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ecns_approved',
        verbose_name=_("Approved By")
    )
    
    status = models.CharField(
        max_length=20,
        choices=ECNStatus.choices,
        default=ECNStatus.DRAFT,
        verbose_name=_("ECN Status")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Engineering Change Request")
        verbose_name_plural = _("Engineering Change Requests")

    def __str__(self):
        return f"{self.ecn_number or 'Draft ECN'} - {self.project.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if not self.ecn_number:
            from django.utils import timezone
            date_val = self.ecn_date or timezone.now().date()
            year = date_val.strftime('%y')
            month = date_val.strftime('%m')
            prefix = f"ECN/{year}/{month}/"
            
            # Find the last ECN that starts with this prefix
            last_ecn = ECN.objects.filter(ecn_number__startswith=prefix).order_by('ecn_number').last()
            
            if last_ecn:
                try:
                    last_serial = int(last_ecn.ecn_number.split('/')[-1])
                    new_serial = last_serial + 1
                except (ValueError, IndexError):
                    new_serial = 1
            else:
                new_serial = 1
                
            self.ecn_number = f"{prefix}{new_serial:03d}"
            
        super().save(*args, **kwargs)

        # 1. Automatically change project status from 'Closed' to 'Open' on new ECN creation
        project = self.project
        if is_new and project.status == 'Closed':
            project.status = 'Open'
            project.save(update_fields=['status'])

        # 2. Automatically change project status back to 'Closed' once ECN is approved
        if self.status == ECNStatus.APPROVED or self.status == 'Approved':
            if project.status != 'Closed':
                project.status = 'Closed'
                project.save(update_fields=['status'])


class CustomerFeedback(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_("Project")
    )
    form_no = models.CharField(max_length=50, default='DD-F-11', verbose_name=_("Form No."))
    form_revision_no = models.CharField(max_length=50, default='Rev-00', verbose_name=_("Form Revision No."))
    form_issue_date = models.DateField(default='2025-07-01', verbose_name=_("Form Issue Date"))
    
    # Section 1: Project & Customer Details
    customer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Customer Name"))
    product_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Product / Project Name"))
    customer_drawing_no = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Customer Part / Drawing Number"))
    pcepl_part_no = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("PCEPL Part Number"))
    panel_dispatch_date = models.DateField(blank=True, null=True, verbose_name=_("Panel / Product Dispatch Date"))
    feedback_collection_date = models.DateField(blank=True, null=True, verbose_name=_("Feedback Collection Date"))
    usage_duration_months = models.PositiveIntegerField(default=12, blank=True, null=True, verbose_name=_("Usage Duration (Months)"))
    
    # Section 2: Performance Feedback (Based on Usage)
    performance_feedback = models.JSONField(default=list, blank=True, verbose_name=_("Performance Feedback"))
    
    # Section 3: Feedback Provided By (Customer Rep.)
    customer_rep_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Customer Rep Name"))
    customer_rep_signature = models.TextField(blank=True, null=True, verbose_name=_("Customer Rep Signature"))
    customer_rep_date = models.DateField(blank=True, null=True, verbose_name=_("Customer Rep Sign Date"))
    
    # Section 4: Reviewed By (PCEPL Rep.)
    pcepl_rep_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("PCEPL Rep Name"))
    pcepl_rep_signature = models.TextField(blank=True, null=True, verbose_name=_("PCEPL Rep Signature"))
    pcepl_rep_date = models.DateField(blank=True, null=True, verbose_name=_("PCEPL Rep Sign Date"))
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('Scheduled', _('Scheduled')),
            ('Pending', _('Pending')),
            ('Submitted', _('Submitted')),
        ],
        default='Scheduled',
        verbose_name=_("Status")
    )
    scheduled_date = models.DateField(verbose_name=_("Scheduled Date"))
    notified = models.BooleanField(default=False, verbose_name=_("Notified"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = _("Customer Feedback")
        verbose_name_plural = _("Customer Feedbacks")

    def __str__(self):
        return f"Feedback for {self.project.pid} - Scheduled: {self.scheduled_date}"


