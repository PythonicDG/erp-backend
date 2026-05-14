from django.utils import timezone
from .models import Project, ActivityLog

class ProjectService:
    @staticmethod
    def generate_pid(date_received=None):
        if not date_received:
            date_received = timezone.now().date()
        
        year = date_received.strftime('%y')
        month = date_received.strftime('%m')
        prefix = f"PRJ/{year}/{month}/"
        
        last_project = Project.objects.filter(pid__startswith=prefix).order_by('pid').last()
        
        if last_project:
            try:
                last_serial = int(last_project.pid.split('/')[-1])
                new_serial = last_serial + 1
            except (ValueError, IndexError):
                new_serial = 1
        else:
            new_serial = 1
            
        return f"{prefix}{new_serial:03d}"

    @staticmethod
    def get_month_received_string(date_received):
        return date_received.strftime('%B %Y')

    @staticmethod
    def initialize_workflow(project):
        """
        Uses dynamic WorkflowService to initialize stages.
        """
        from workflow.services import WorkflowService
        WorkflowService.initialize_project_workflow(project)

    @staticmethod
    def log_activity(project, user, action, details=None):
        return ActivityLog.objects.create(
            project=project,
            user=user,
            action=action,
            details=details or {}
        )
