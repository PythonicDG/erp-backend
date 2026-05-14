import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from authentication.system_models import AuditLog, CompanyProfile

print(f"Total Audit Logs: {AuditLog.objects.count()}")
for log in AuditLog.objects.all()[:5]:
    print(f"Log: {log.action} - {log.target} - {log.timestamp}")

profile = CompanyProfile.objects.first()
if profile:
    print(f"Audit Logs Enabled: {profile.audit_logs_enabled}")
else:
    print("No Company Profile found")
