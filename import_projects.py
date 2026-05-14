import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from projects.models import Project
from workflow.services import WorkflowService
from django.contrib.auth import get_user_model

User = get_user_model()

def bulk_import():
    # Get an admin user to assign as creator
    admin_user = User.objects.filter(is_superuser=True).first()
    
    projects_data = [
        {"name": "JUNCTION BOX CSL-WATERJET", "customer": "WARTSILA INDIA LTD.", "c_part": "PAAG464305", "p_part": "30071850", "type": "OTHER", "auth": "Internal QA", "date": "2025-03-03"},
        {"name": "Mena", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "F6.M828.02.0.PR", "p_part": "30071982", "type": "LCP", "auth": "Internal QA", "date": "2025-03-04"},
        {"name": "Mena", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "F6.M828.03.0.PR", "p_part": "30071985", "type": "EWH", "auth": "Internal QA", "date": "2025-03-04"},
        {"name": "18 KW RORO", "customer": "SIGMA POWER CONTROL SYSTEM", "c_part": "", "p_part": "30072003", "type": "LCP", "auth": "IRS", "date": "2025-03-04"},
        {"name": "350 KW MDL NGOPV", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "DV0.M810.02.0.PR", "p_part": "30072257", "type": "LCP", "auth": "Internal QA", "date": "2025-03-09"},
        {"name": "25KVA UTS", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "3H.M812.02.0.PR", "p_part": "30072067", "type": "LCP", "auth": "Internal QA", "date": "2025-03-19"},
        {"name": "100KVA Neithal Boat", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "6H.M829.02.0.PR", "p_part": "30072054", "type": "LCP", "auth": "Internal QA", "date": "2025-03-24"},
        {"name": "82.5 KVA NEITHAL BOAT", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "6H.M829.02.0.00", "p_part": "30072054", "type": "LCP", "auth": "Internal QA", "date": "2025-03-26"},
        {"name": "ELGI", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "02.M811.02.0.00", "p_part": "30072057", "type": "LCP", "auth": "Internal QA", "date": "2025-03-26"},
        {"name": "MANDOVI", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "F6.M819.02.0.00", "p_part": "30069981", "type": "LCP", "auth": "Internal QA", "date": "2025-03-28"},
        {"name": "KAMAT ENERGY 83BHP", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "4H.M856.03.0.PR", "p_part": "30072074", "type": "EWH", "auth": "Internal QA", "date": "2025-03-28"},
        {"name": "NGOPV", "customer": "WARTSILA INDIA LTD.", "c_part": "", "p_part": "30072075", "type": "OTHER", "auth": "Internal QA", "date": "2025-04-09"},
        {"name": "1 MW SHAFT GENRATOR", "customer": "ELMOT ALTERNATORS PVT LTD", "c_part": "NA", "p_part": "30072103", "type": "LCP", "auth": "IRS", "date": "2025-04-22"},
        {"name": "DEFFENCE PROJECT", "customer": "KIRLOSKAR OIL ENGINES LTD.", "c_part": "3H.6275.90.0.PR", "p_part": "", "type": "OTHER", "auth": "Internal QA", "date": "2025-05-21"},
    ]

    for item in projects_data:
        project = Project.objects.create(
            name=item['name'],
            customer_name=item['customer'],
            customer_part_no=item['c_part'],
            pcepl_part_no=item['p_part'],
            project_type=item['type'],
            inspection_authority=item['auth'],
            date_received=item['date'],
            status='Open',
            created_by=admin_user
        )
        # Automatically initialize workflow stages for each project
        WorkflowService.initialize_project_workflow(project)
        print(f"✅ Created: {project.pid} - {project.name}")

if __name__ == "__main__":
    bulk_import()
