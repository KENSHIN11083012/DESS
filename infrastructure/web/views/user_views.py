"""
Vistas de Usuario - DESS
Responsable de dashboards, soluciones y funcionalidades de usuario regular
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess
from infrastructure.security.permissions import user_only_required, solution_access_required
from ..utils import ListViewHelper, AuditHelper

logger = logging.getLogger(__name__)


@user_only_required
def user_dashboard_view(request):
    """Dashboard para usuarios regulares - redirige a soluciones del usuario"""
    # En lugar de un dashboard separado, redirigimos a las soluciones del usuario
    return redirect('user_solutions')


@user_only_required
def user_solutions_view(request):
    """Vista de soluciones para usuarios regulares con filtrado"""
    # Obtener parámetros de filtrado
    search = request.GET.get('search', '').strip()
    solution_type = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    
    # Consulta base optimizada - soluciones asignadas al usuario
    assignments_query = UserSolutionAssignment.objects.for_user(request.user).active().with_related_info()
    
    # Aplicar filtros de búsqueda
    if search:
        assignments_query = assignments_query.filter(
            Q(solution__name__icontains=search) |
            Q(solution__description__icontains=search) |
            Q(solution__version__icontains=search)
        )
    
    # Aplicar filtro por tipo
    if solution_type:
        assignments_query = assignments_query.filter(solution__solution_type=solution_type)
    
    # Aplicar filtro por estado
    if status:
        assignments_query = assignments_query.filter(solution__status=status)
    
    # Ordenar por fecha de asignación (más recientes primero)
    assignments = assignments_query.order_by('-assigned_at')
    
    # Calcular estadísticas
    all_assignments = UserSolutionAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('solution')
    
    total_assigned = all_assignments.count()
    ready_solutions = all_assignments.filter(
        solution__status='active', 
        solution__access_url__isnull=False
    ).exclude(solution__access_url='').count()
    configuring_solutions = all_assignments.filter(
        Q(solution__status='active', solution__access_url__isnull=True) |
        Q(solution__status='active', solution__access_url='') |
        Q(solution__status='deployed')
    ).count()
    maintenance_solutions = all_assignments.filter(solution__status='maintenance').count()
    
    # Construir contexto
    context = {
        'user': request.user,
        'page_title': 'Mis Soluciones',
        'user_solutions': assignments,
        'solutions_stats': {
            'total_assigned': total_assigned,
            'ready_solutions': ready_solutions,
            'configuring_solutions': configuring_solutions,
            'maintenance_solutions': maintenance_solutions,
            'recent_accesses': 0,  # TODO: implementar después
            'favorite_count': 0    # TODO: implementar favoritos después
        },
        'search_query': search,
        'selected_type': solution_type,
        'selected_status': status,
    }
    
    return render(request, 'dashboard/user_solutions.html', context)


@solution_access_required
def solution_access_view(request, solution_id):
    """Vista para acceder a una solución específica"""
    solution = get_object_or_404(Solution, id=solution_id)
    
    # Registrar acceso usando helper de auditoría
    AuditHelper.log_solution_access(
        user=request.user,
        solution=solution,
        ip_address=request.META.get('REMOTE_ADDR', '')
    )
    
    # Redirigir a la solución
    if solution.access_url and solution.status == 'active':
        return redirect(solution.access_url)
    else:
        messages.error(request, 'La solución no está disponible en este momento')
        return redirect('user_solutions')


@user_only_required
def user_profile_view(request):
    """Vista de perfil de usuario"""
    context = {
        'user': request.user,
        'page_title': 'Mi Perfil',
    }
    
    return render(request, 'dashboard/user_profile.html', context)