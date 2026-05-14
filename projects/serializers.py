from rest_framework import serializers
from .models import Project, WorkflowStage, ActivityLog
from .services import ProjectService

class WorkflowStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStage
        fields = ['id', 'name', 'order', 'status', 'unlocked_at', 'completed_at']

class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.get_full_name')

    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'details', 'timestamp', 'user_name']

class ProjectSerializer(serializers.ModelSerializer):
    pid = serializers.CharField(read_only=True)
    month_received = serializers.CharField(read_only=True)
    current_stage = serializers.SerializerMethodField()
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
 
    class Meta:
        model = Project
        fields = [
            'id', 'pid', 'name', 'customer_name', 'customer_part_no', 
            'pcepl_part_no', 'project_type', 'inspection_authority', 
            'applicable_standard', 'date_received', 'month_received', 
            'target_completion_date', 'status', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'current_stage'
        ]
        read_only_fields = ['created_by']
 
    def get_current_stage(self, obj):
        from workflow.models import StageInstance
        # Get the first stage that is not approved
        current = obj.workflow_stages.filter(
            status__in=['Unlocked', 'In Progress', 'Submitted', 'Rejected']
        ).order_by('order').first()
        
        if current:
            return current.template.name
        
        # If all approved, maybe show 'Completed'
        if obj.status == 'Closed':
            return "Project Completed"
            
        return "Not Started"

    def create(self, validated_data):
        # Assign current user as creator
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        project = super().create(validated_data)
        
        # Initialize workflow
        ProjectService.initialize_workflow(project)
        
        # Log activity
        ProjectService.log_activity(
            project, 
            request.user if request else None, 
            "Project Created",
            {"status": project.status}
        )
        
        return project
