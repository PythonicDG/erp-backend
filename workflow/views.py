from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from projects.models import Project
from authentication.models import User
from .models import StageTemplate, FormField, StageInstance, StageSubmission
from .serializers import StageTemplateSerializer, FormFieldSerializer, StageInstanceSerializer, StageSubmissionSerializer
from .services import WorkflowService

from authentication.mixins import AuditLogMixin
from authentication.permissions import IsAdmin

class StageTemplateViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = StageTemplate.objects.all().prefetch_related('fields')
    serializer_class = StageTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_module = "Workflow"

    def get_audit_target(self, instance):
        return f"Workflow Stage: {instance.name}"

    @decorators.action(detail=True, methods=['post'])
    def sync_fields(self, request, pk=None):
        template = self.get_object()
        fields_data = request.data.get('fields', [])
        
        # Simple bulk sync: delete existing and recreat (or update if ID provided)
        # For simplicity in this engine, we'll replace the fields
        template.fields.all().delete()
        
        created_fields = []
        for i, field_data in enumerate(fields_data):
            field = FormField.objects.create(
                stage_template=template,
                name=field_data.get('name') or f"field_{i}",
                label=field_data.get('label'),
                field_type=field_data.get('field_type'),
                section=field_data.get('section'),
                order=i,
                configuration=field_data.get('configuration', {}),
                options=field_data.get('options', []),
                is_required=field_data.get('is_required', False)
            )
            created_fields.append(field)
            
        from authentication.utils import log_action
        log_action(
            user=request.user,
            action="SYNC_FIELDS",
            target=f"Form for Stage: {template.name}",
            module="Workflow"
        )
            
        return Response(FormFieldSerializer(created_fields, many=True).data)

    @decorators.action(detail=False, methods=['post'])
    def reorder(self, request):
        orders = request.data.get('orders', [])
        if not orders:
            return Response({"error": "Orders are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.db import transaction
        with transaction.atomic():
            # Update all StageTemplates order
            for item in orders:
                StageTemplate.objects.filter(id=item['id']).update(order=item['order'])
                # Propagate order changes to all existing projects' StageInstances
                StageInstance.objects.filter(template_id=item['id']).update(order=item['order'])
            
            # Recalculate timeline dates for all projects that are not Closed
            active_projects = Project.objects.exclude(status='Closed')
            for proj in active_projects:
                WorkflowService.recalculate_project_timeline(proj)
                
        # Audit Log
        from authentication.utils import log_action
        log_action(
            user=request.user,
            action="REORDER_STAGES",
            target="Workflow Stages Sequence",
            module="Workflow"
        )
        
        return Response({"status": "reordered"})


class StageInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StageInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                # Auto-sync missing stages from templates
                WorkflowService.initialize_project_workflow(project)
            except Project.DoesNotExist:
                pass
                
            return StageInstance.objects.filter(project_id=project_id)\
                .select_related('template', 'project')\
                .prefetch_related('submissions', 'activities', 'template__fields')
            
        return StageInstance.objects.all()\
            .select_related('template', 'project')\
            .prefetch_related('submissions', 'activities', 'template__fields')

    @decorators.action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        stage_instance = self.get_object()
        data = request.data.get('data')
        is_final = request.data.get('is_final', True)
        
        if not data:
            return Response({"error": "Data is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        submission = WorkflowService.submit_stage(stage_instance, request.user, data, is_final)
        return Response(StageSubmissionSerializer(submission).data)

    @decorators.action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        stage_instance = self.get_object()
        remarks = request.data.get('remarks')
        
        if request.user.role not in ['ADMIN', 'SUPERVISOR', 'SUPERADMIN']:
             return Response({"error": "Only supervisors or admins can approve"}, status=status.HTTP_403_FORBIDDEN)
             
        WorkflowService.approve_stage(stage_instance, request.user, remarks)
        return Response({"status": "approved"})

    @decorators.action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        stage_instance = self.get_object()
        remarks = request.data.get('remarks')
        
        if not remarks:
            return Response({"error": "Remarks are required for rejection"}, status=status.HTTP_400_BAD_REQUEST)
            
        if request.user.role not in ['ADMIN', 'SUPERVISOR', 'SUPERADMIN']:
             return Response({"error": "Only supervisors or admins can reject"}, status=status.HTTP_403_FORBIDDEN)
             
        WorkflowService.reject_stage(stage_instance, request.user, remarks)
        return Response({"status": "rejected"})
