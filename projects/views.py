from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project
from .serializers import ProjectSerializer
from .permissions import CanCreateProject

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('stages', 'activities')
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['status', 'project_type', 'customer_name']
    search_fields = ['pid', 'name', 'customer_name', 'customer_part_no', 'pcepl_part_no']
    ordering_fields = ['date_received', 'target_completion_date', 'created_at', 'pid']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [CanCreateProject()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def sync_all_statuses(self, request):
        from workflow.models import StageInstance
        projects = Project.objects.exclude(status='Closed')
        updated_count = 0
        for project in projects:
            instances = StageInstance.objects.filter(project=project)
            if instances.exists() and all(inst.status == 'Approved' for inst in instances):
                project.status = 'Closed'
                project.save()
                updated_count += 1
        return Response({"message": f"Updated {updated_count} projects"})

    @action(detail=True, methods=['get'])
    def full_report(self, request, pk=None):
        from workflow.models import StageInstance
        from workflow.serializers import StageInstanceSerializer
        from authentication.system_models import CompanyProfile
        from authentication.serializers import CompanyProfileSerializer
        
        project = self.get_object()
        stages = StageInstance.objects.filter(project=project).order_by('order')
        company = CompanyProfile.objects.first()
        
        return Response({
            "project": ProjectSerializer(project).data,
            "stages": StageInstanceSerializer(stages, many=True).data,
            "company": CompanyProfileSerializer(company).data if company else None
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from django.db.models import Count
        stats = Project.objects.values('status').annotate(count=Count('id'))
        return Response(stats)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from django.db.models import Count, Q
        from django.db.models.functions import TruncMonth
        from authentication.system_models import SystemConfiguration
        
        user = request.user
        
        # All users see all projects for full transparency
        projects_qs = Project.objects.all()
            
        # 1. Quick Stats
        total_projects = projects_qs.count()
        closed_projects = projects_qs.filter(status='Closed').count()
        open_projects = projects_qs.filter(status__in=['Open', 'In Progress']).count()
        customers_count = projects_qs.values('customer_name').distinct().count()
        
        completion_rate = (closed_projects / total_projects * 100) if total_projects > 0 else 0
        
        # 2. Project Type Distribution (Pie Chart)
        type_distribution = projects_qs.values('project_type').annotate(count=Count('id')).order_by('count')
        
        # 2.5 Stage-wise Distribution for Open Projects
        from workflow.models import StageInstance, StageTemplate
        active_projects_ids = projects_qs.filter(status__in=['Open', 'In Progress']).values_list('id', flat=True)
        
        # Get count of projects at each stage (where that stage is the current one)
        # Current stage is defined as the first 'Unlocked' or 'In Progress' stage
        stage_distribution = []
        templates = StageTemplate.objects.filter(is_active=True).order_by('order')
        
        for template in templates:
            # Count projects where this template is their first non-approved stage
            count = 0
            # This is slightly complex in SQL, so we'll approximate: 
            # Count projects where this stage instance is UNLOCKED or SUBMITTED
            count = StageInstance.objects.filter(
                template=template,
                project_id__in=active_projects_ids,
                status__in=['Unlocked', 'In Progress', 'Submitted', 'Rejected']
            ).count()
            
            if count > 0:
                stage_distribution.append({
                    'name': template.name,
                    'count': count
                })
                
        # 3. Monthly Trend (Bar/Line Chart)
        monthly_trend = projects_qs.annotate(
            month=TruncMonth('date_received')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # 4. Recent Projects (Table)
        recent_projects = projects_qs.select_related('created_by').order_by('-created_at')[:10]
        recent_data = ProjectSerializer(recent_projects, many=True).data
        
        # 5. System Info (Only for Admins/Supervisors, or limited for employees)
        sys_config = SystemConfiguration.objects.first()
        if not sys_config:
            sys_config = SystemConfiguration.objects.create()
            
        dashboard_data = {
            'stats': {
                'total': total_projects,
                'closed': closed_projects,
                'open': open_projects,
                'customers': customers_count,
                'completion_rate': round(completion_rate, 2)
            },
            'charts': {
                'type_distribution': list(type_distribution),
                'stage_distribution': stage_distribution,
                'monthly_trend': [
                    {'month': item['month'].strftime('%b %Y'), 'count': item['count']} 
                    for item in monthly_trend if item['month']
                ]
            },
            'recent_projects': recent_data,
        }
        
        # Add system info for Admins/Supervisors
        if user.role in ['ADMIN', 'SUPERVISOR']:
            dashboard_data['system_info'] = {
                'company': sys_config.company_name,
                'financial_year': sys_config.financial_year,
                'version': sys_config.system_version,
                'last_update': sys_config.last_update,
                'server': sys_config.server_info
            }
        else:
            dashboard_data['system_info'] = {
                'company': sys_config.company_name,
                'financial_year': sys_config.financial_year,
                'version': sys_config.system_version,
                'last_update': sys_config.last_update,
            }
            
        return Response(dashboard_data)
