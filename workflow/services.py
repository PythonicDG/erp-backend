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
                
        # Recalculate project timeline automatically upon initialization
        WorkflowService.recalculate_project_timeline(project)

    @staticmethod
    def recalculate_project_timeline(project):
        """
        Recalculates the planned start and end dates for all StageInstances
        sequentially based on the project complexity and start date.
        """
        if not project.planned_start_date:
            # If no start date, we reset or clear planned dates
            StageInstance.objects.filter(project=project).update(
                planned_start_date=None,
                planned_end_date=None,
                duration=None
            )
            return

        from datetime import timedelta
        instances = StageInstance.objects.filter(project=project).order_by('order')
        
        current_start_date = project.planned_start_date
        complexity = project.project_complexity or 'Medium'

        for instance in instances:
            template = instance.template
            if complexity == 'High':
                duration = template.duration_high
            elif complexity == 'Low':
                duration = template.duration_low
            else:
                duration = template.duration_medium

            # Calculate planned end date
            if duration and duration > 0:
                planned_end_date = current_start_date + timedelta(days=duration)
            else:
                planned_end_date = current_start_date
                duration = 0

            instance.planned_start_date = current_start_date
            instance.planned_end_date = planned_end_date
            instance.duration = duration
            instance.save()

            # The next stage starts on the calendar day after current_end_date, skipping Sunday
            next_start = planned_end_date + timedelta(days=1)
            if next_start.weekday() == 6:  # 6 is Sunday in Python
                next_start += timedelta(days=1)  # Skip Sunday and set to Monday
            current_start_date = next_start

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
        
        # Populate live tracking fields for the D&D Plan
        stage_instance.actual_completion_date = timezone.now().date()
        if stage_instance.planned_end_date:
            delay = (stage_instance.actual_completion_date - stage_instance.planned_end_date).days
            stage_instance.delay_days = max(0, delay)
        else:
            stage_instance.delay_days = 0
            
        if remarks:
            stage_instance.remarks = remarks
            
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
