from .utils import log_action

class AuditLogMixin:
    """
    Mixin to automatically log CREATE, UPDATE, and DELETE actions.
    Requires 'audit_module' to be defined on the ViewSet.
    """
    audit_module = "General"

    def get_audit_target(self, instance):
        return str(instance)

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action="CREATE",
            target=self.get_audit_target(instance),
            module=self.audit_module
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action="UPDATE",
            target=self.get_audit_target(instance),
            module=self.audit_module
        )

    def perform_destroy(self, instance):
        target = self.get_audit_target(instance)
        instance.delete()
        log_action(
            user=self.request.user,
            action="DELETE",
            target=target,
            module=self.audit_module
        )
