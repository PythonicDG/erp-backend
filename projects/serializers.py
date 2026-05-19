from rest_framework import serializers
from .models import Project, CustomerMaster, StandardMaster, InspectionAuthorityMaster, ECN
from .services import ProjectService

class CustomerMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerMaster
        fields = '__all__'

class StandardMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardMaster
        fields = '__all__'

class InspectionAuthorityMasterSerializer(serializers.ModelSerializer):
    applicable_standard_details = StandardMasterSerializer(source='applicable_standard', read_only=True)
    applicable_standard_name = serializers.ReadOnlyField(source='applicable_standard.standard_name')

    class Meta:
        model = InspectionAuthorityMaster
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    pid = serializers.CharField(read_only=True)
    month_received = serializers.CharField(read_only=True)
    current_stage = serializers.SerializerMethodField()
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    customer_details = CustomerMasterSerializer(source='customer', read_only=True)
    standard_details = StandardMasterSerializer(source='standard', read_only=True)
    inspection_authority_details = InspectionAuthorityMasterSerializer(source='inspection_authority_fk', read_only=True)
 
    class Meta:
        model = Project
        fields = [
            'id', 'pid', 'name', 'customer', 'customer_details', 'customer_name', 'customer_part_no', 
            'pcepl_part_no', 'project_type', 'inspection_authority', 'inspection_authority_fk', 'inspection_authority_details',
            'applicable_standard', 'standard', 'standard_details', 'date_received', 'month_received', 
            'target_completion_date', 'status', 'priority', 'description', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'current_stage', 'assigned_employee'
        ]
        read_only_fields = ['created_by']
 
    def validate_project_type(self, value):
        valid_types = [
            'OTHER', 'LCP', 'EWH', 'RCP', 'SP', 'AWH', 
            'JB', 'BATTERY CABLE', 'DROP IN PLATE', 'BATTERY BOX'
        ]
        val_upper = str(value).strip().upper()
        if val_upper not in valid_types:
            # Maintain compatibility for existing records
            if val_upper in ['STANDARD', 'CUSTOM', 'MAINTENANCE']:
                return val_upper
            raise serializers.ValidationError(
                f"Invalid project type. Allowed types are: {', '.join(valid_types)}"
            )
        return val_upper

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


class ECNSerializer(serializers.ModelSerializer):
    ecn_number = serializers.CharField(read_only=True)
    customer_name = serializers.SerializerMethodField()
    product_name = serializers.ReadOnlyField(source='project.name')
    customer_part_no = serializers.ReadOnlyField(source='project.customer_part_no')
    pcepl_part_no = serializers.ReadOnlyField(source='project.pcepl_part_no')
    applicable_standard = serializers.ReadOnlyField(source='project.applicable_standard')
    inspection_authority = serializers.ReadOnlyField(source='project.inspection_authority')
    
    # User full names for read
    initiator_name = serializers.ReadOnlyField(source='initiator.full_name')
    reviewed_by_name = serializers.ReadOnlyField(source='reviewed_by.full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.full_name')
    
    # Project detail fields for list view
    project_pid = serializers.ReadOnlyField(source='project.pid')
    project_name = serializers.ReadOnlyField(source='project.name')
    
    class Meta:
        model = ECN
        fields = [
            'id', 'ecn_number', 'project', 'project_pid', 'project_name',
            'customer_name', 'product_name', 'customer_part_no', 'pcepl_part_no',
            'applicable_standard', 'inspection_authority', 'raised_department',
            'change_initiated_by', 'ecn_date', 'old_revision_no', 'old_revision_date',
            'new_revision', 'details_of_change', 'impact_analysis', 'action_plan',
            'initiator', 'initiator_name', 'reviewed_by', 'reviewed_by_name',
            'approved_by', 'approved_by_name', 'status', 'created_at', 'updated_at'
        ]
        
    def get_customer_name(self, obj):
        if obj.project:
            if obj.project.customer:
                return obj.project.customer.name
            return obj.project.customer_name or ''
        return ''
