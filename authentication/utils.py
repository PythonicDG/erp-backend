from .system_models import AuditLog, CompanyProfile

def log_action(user, action, target, module, status='SUCCESS'):
    """
    Utility function to record system-wide audit logs.
    """
    try:
        # Extremely simplified for debugging
        return AuditLog.objects.create(
            user=user,
            action=action,
            target=target,
            module=module,
            status=status
        )
    except Exception as e:
        # Try logging to console at least
        print(f"CRITICAL: Audit log failed: {str(e)}")
        return None

def notify_user(recipient, title, message, notification_type='info', sender=None, link=None):
    """
    Utility function to create in-app notifications.
    """
    from .models import Notification
    try:
        return Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
    except Exception as e:
        print(f"CRITICAL: Notification failed: {str(e)}")
        return None
