import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from projects.models import Project
from workflow.models import StageInstance

def sync_project_statuses():
    projects = Project.objects.exclude(status='Closed')
    updated_count = 0
    
    for project in projects:
        instances = StageInstance.objects.filter(project=project)
        if not instances.exists():
            continue
            
        # Check if all instances are Approved
        all_approved = all(inst.status == StageInstance.Status.APPROVED for inst in instances)
        
        if all_approved:
            project.status = 'Closed'
            project.save()
            updated_count += 1
            print(f"Project '{project.name}' ({project.pid}) marked as Closed.")
            
    print(f"\nSuccessfully updated {updated_count} projects.")

if __name__ == "__main__":
    sync_project_statuses()
