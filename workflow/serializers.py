from rest_framework import serializers
from .models import StageTemplate, FormField, StageInstance, StageSubmission, StageActivity

class FormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField
        fields = [
            'id', 'section', 'label', 'name', 'field_type', 'placeholder', 
            'default_value', 'is_required', 'min_length', 'max_length', 
            'is_readonly', 'order', 'options', 'configuration'
        ]

class StageTemplateSerializer(serializers.ModelSerializer):
    fields = FormFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = StageTemplate
        fields = [
            'id', 'name', 'code', 'description', 'order', 
            'is_mandatory', 'is_active', 'assigned_role', 
            'approval_required', 'allow_attachments', 'fields',
            'duration_high', 'duration_medium', 'duration_low'
        ]

class StageSubmissionSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.ReadOnlyField(source='submitted_by.full_name')
    
    class Meta:
        model = StageSubmission
        fields = ['id', 'submitted_by', 'submitted_by_name', 'data', 'status', 'remarks', 'submitted_at']

class StageActivitySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.ReadOnlyField(source='performed_by.full_name')
    
    class Meta:
        model = StageActivity
        fields = ['id', 'performed_by_name', 'action', 'remarks', 'timestamp']

class StageInstanceSerializer(serializers.ModelSerializer):
    template_details = StageTemplateSerializer(source='template', read_only=True)
    current_submission = serializers.SerializerMethodField()
    activities = StageActivitySerializer(many=True, read_only=True)

    class Meta:
        model = StageInstance
        fields = [
            'id', 'template', 'template_details', 'status', 'order', 
            'unlocked_at', 'completed_at', 'current_submission', 'activities',
            'planned_start_date', 'planned_end_date', 'duration', 
            'actual_completion_date', 'delay_days', 'remarks'
        ]

    def get_current_submission(self, obj):
        submission = obj.submissions.order_by('-submitted_at').first()
        if submission:
            return StageSubmissionSerializer(submission).data
        return None
