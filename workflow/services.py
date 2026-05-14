from django.utils import timezone
from django.db import transaction
from .models import StageTemplate, StageInstance, StageSubmission, StageActivity
from projects.models import Project
from authentication.system_models import AuditLog
from authentication.utils import notify_user
from authentication.models import User

class WorkflowService:
    @staticmethod
    def initialize_project_workflow(project):
        """
        Syncs StageInstances for a project based on active StageTemplates.
        Adds missing stages and ensures the first one is unlocked if none are.
        """
        templates = StageTemplate.objects.filter(is_active=True).order_by('order')
        
        if not templates.exists():
            return
            
        existing_template_ids = StageInstance.objects.filter(project=project).values_list('template_id', flat=True)
        
        for i, template in enumerate(templates):
            if template.id not in existing_template_ids:
                # If this is the absolute first stage being added to this project, unlock it
                # Otherwise, lock it (it will unlock as previous stages finish)
                is_first_overall = not StageInstance.objects.filter(project=project).exists()
                
                status = StageInstance.Status.UNLOCKED if (is_first_overall and i == 0) else StageInstance.Status.LOCKED
                unlocked_at = timezone.now() if (is_first_overall and i == 0) else None
                
                StageInstance.objects.create(
                    project=project,
                    template=template,
                    order=template.order,
                    status=status,
                    unlocked_at=unlocked_at
                )

    @staticmethod
    @transaction.atomic
    def submit_stage(stage_instance, user, data, is_final=True):
        """
        Handles form submission for a stage.
        """
        submission, created = StageSubmission.objects.update_or_create(
            stage_instance=stage_instance,
            status=StageSubmission.SubmissionStatus.DRAFT,
            defaults={
                'submitted_by': user,
                'data': data,
            }
        )
        
        if is_final:
            submission.status = StageSubmission.SubmissionStatus.SUBMITTED
            submission.save()
            
            stage_instance.status = StageInstance.Status.PENDING_APPROVAL
            stage_instance.save()

            # Update Project Status for global tracking
            project = stage_instance.project
            project.status = 'Pending Approval'
            project.save()
            
            StageActivity.objects.create(
                stage_instance=stage_instance,
                performed_by=user,
                action="Stage Submitted"
            )

            # Log Audit Event
            AuditLog.objects.create(
                user=user,
                action=f"Submitted Stage: {stage_instance.template.name}",
                target=f"PID: {stage_instance.project.pid}",
                module="Workflow",
                status="SUCCESS"
            )

            # Notify all Supervisors and Admins
            recipients = list(User.objects.filter(role__in=['ADMIN', 'SUPERVISOR']))
            if stage_instance.project.supervisor and stage_instance.project.supervisor not in recipients:
                recipients.append(stage_instance.project.supervisor)

            for recipient in recipients:
                notify_user(
                    recipient=recipient,
                    sender=user,
                    title="Approval Request",
                    message=f"{user.full_name} submitted {stage_instance.template.name} for project {stage_instance.project.pid}",
                    notification_type='approval_request',
                    link=f"/projects/{stage_instance.project.id}"
                )
            
        return submission

    @staticmethod
    @transaction.atomic
    def approve_stage(stage_instance, supervisor, remarks=None):
        """
        Approves a stage and unlocks the next one.
        """
        stage_instance.status = StageInstance.Status.APPROVED
        stage_instance.completed_at = timezone.now()
        stage_instance.save()
        
        # Update submission status
        submission = stage_instance.submissions.filter(status=StageSubmission.SubmissionStatus.SUBMITTED).last()
        if submission:
            submission.status = StageSubmission.SubmissionStatus.APPROVED
            submission.remarks = remarks
            submission.save()
            
        StageActivity.objects.create(
            stage_instance=stage_instance,
            performed_by=supervisor,
            action="Stage Approved",
            remarks=remarks
        )

        # Log Audit Event
        AuditLog.objects.create(
            user=supervisor,
            action=f"Approved Stage: {stage_instance.template.name}",
            target=f"PID: {stage_instance.project.pid}",
            module="Workflow",
            status="SUCCESS"
        )
        
        # Notify the submitter
        last_submission = stage_instance.submissions.order_by('-submitted_at').first()
        if last_submission:
            notify_user(
                recipient=last_submission.submitted_by,
                sender=supervisor,
                title="Stage Approved",
                message=f"Your submission for {stage_instance.template.name} has been approved. {f'Remarks: {remarks}' if remarks else ''}",
                notification_type='success',
                link=f"/projects/{stage_instance.project.id}"
            )
        
        # Unlock next stage
        next_stage = StageInstance.objects.filter(
            project=stage_instance.project, 
            order__gt=stage_instance.order
        ).order_by('order').first()
        
        if next_stage:
            next_stage.status = StageInstance.Status.UNLOCKED
            next_stage.unlocked_at = timezone.now()
            next_stage.save()
            
            # Reset project status to In Progress
            project = stage_instance.project
            project.status = 'In Progress'
            project.save()
        else:
            # All stages completed, mark project as Closed
            project = stage_instance.project
            project.status = 'Closed'
            project.save()

    @staticmethod
    @transaction.atomic
    def reject_stage(stage_instance, supervisor, remarks):
        """
        Rejects a stage and sends it back to employee.
        """
        stage_instance.status = StageInstance.Status.REJECTED
        stage_instance.save()
        
        # Update Project Status
        project = stage_instance.project
        project.status = 'Rejected'
        project.save()
        
        submission = stage_instance.submissions.filter(status=StageSubmission.SubmissionStatus.SUBMITTED).last()
        if submission:
            submission.status = StageSubmission.SubmissionStatus.REJECTED
            submission.remarks = remarks
            submission.save()
            
        StageActivity.objects.create(
            stage_instance=stage_instance,
            performed_by=supervisor,
            action="Stage Rejected",
            remarks=remarks
        )

        # Log Audit Event
        AuditLog.objects.create(
            user=supervisor,
            action=f"Rejected Stage: {stage_instance.template.name}",
            target=f"PID: {stage_instance.project.pid}",
            module="Workflow",
            status="SUCCESS"
        )

        # Notify the submitter
        last_submission = stage_instance.submissions.order_by('-submitted_at').first()
        if last_submission:
            notify_user(
                recipient=last_submission.submitted_by,
                sender=supervisor,
                title="Stage Rejected",
                message=f"Your submission for {stage_instance.template.name} has been rejected. Remarks: {remarks}",
                notification_type='error',
                link=f"/projects/{stage_instance.project.id}"
            )
