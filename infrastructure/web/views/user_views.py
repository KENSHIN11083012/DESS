"""
Vistas de Usuario - DESS
Responsable de dashboards, soluciones y funcionalidades de usuario regular
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess, UserFavoriteSolution
from infrastructure.security.permissions import user_only_required, solution_access_required
from ..utils import ListViewHelper, AuditHelper

logger = logging.getLogger(__name__)


@user_only_required
def user_dashboard_view(request):
    """Dashboard principal para usuarios regulares"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from infrastructure.database.models import UserFavoriteSolution
        
        # Obtener estadísticas del usuario
        total_assigned = UserSolutionAssignment.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        ready_solutions = UserSolutionAssignment.objects.filter(
            user=request.user,
            is_active=True,
            solution__status='active',
            solution__access_url__isnull=False
        ).exclude(solution__access_url='').count()
        
        # Obtener soluciones favoritas reales
        favorite_solutions = Solution.objects.filter(
            favorited_by__user=request.user,
            usersolutionassignment__user=request.user,
            usersolutionassignment__is_active=True
        ).select_related().distinct()[:4]  # Máximo 4 favoritos en el dashboard
        
        # Actividad reciente del usuario
        recent_activity = UserSolutionAccess.objects.filter(
            user=request.user
        ).select_related('solution').order_by('-accessed_at')[:10]
        
        # Accesos de esta semana
        week_ago = timezone.now() - timedelta(days=7)
        weekly_accesses = UserSolutionAccess.objects.filter(
            user=request.user,
            accessed_at__gte=week_ago
        ).count()
        
        context = {
            'user': request.user,
            'page_title': 'Panel de Usuario',
            'stats': {
                'total_assigned': total_assigned,
                'ready_solutions': ready_solutions,
                'favorites': favorite_solutions.count(),
                'recent_accesses': weekly_accesses,
            },
            'favorite_solutions': favorite_solutions,
            'recent_activity': recent_activity,
            'notifications_count': 0,  # Se implementará después
            'notifications': [],  # Se implementará después
        }
        
        return render(request, 'dashboard/user_dashboard.html', context)
        
    except Exception as e:
        logger.error(f'Error en user_dashboard_view: {str(e)}')
        messages.error(request, 'Error al cargar el dashboard de usuario')
        return redirect('user_solutions')


@user_only_required
def user_solutions_view(request):
    """Vista de soluciones para usuarios regulares con filtrado y paginación"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Obtener parámetros de filtrado
    search = request.GET.get('search', '').strip()
    solution_type = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    page = request.GET.get('page', 1)
    
    # Obtener preferencia de paginación del usuario (por defecto 12)
    items_per_page = request.session.get('pagination_items_per_page', 12)
    
    # Consulta base optimizada - soluciones asignadas al usuario
    assignments_query = UserSolutionAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('solution', 'assigned_by')
    
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
    assignments_query = assignments_query.order_by('-assigned_at')
    
    # Configurar paginación
    paginator = Paginator(assignments_query, items_per_page)
    
    try:
        assignments_page = paginator.page(page)
    except PageNotAnInteger:
        assignments_page = paginator.page(1)
    except EmptyPage:
        assignments_page = paginator.page(paginator.num_pages)
    
    # Obtener IDs de soluciones favoritas del usuario
    favorite_solution_ids = UserFavoriteSolution.objects.filter(
        user=request.user
    ).values_list('solution_id', flat=True)
    
    # Marcar cuáles son favoritas
    for assignment in assignments_page:
        assignment.solution.is_favorite = assignment.solution.id in favorite_solution_ids
    
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
        'user_solutions': assignments_page,
        'solutions_stats': {
            'total_assigned': total_assigned,
            'ready_solutions': ready_solutions,
            'configuring_solutions': configuring_solutions,
            'maintenance_solutions': maintenance_solutions,
            'recent_accesses': 0,  # TODO: implementar después
            'favorite_count': favorite_solution_ids.count()
        },
        'search_query': search,
        'selected_type': solution_type,
        'selected_status': status,
        'pagination': {
            'current_page': assignments_page.number,
            'total_pages': paginator.num_pages,
            'has_previous': assignments_page.has_previous(),
            'has_next': assignments_page.has_next(),
            'previous_page': assignments_page.previous_page_number() if assignments_page.has_previous() else None,
            'next_page': assignments_page.next_page_number() if assignments_page.has_next() else None,
            'items_per_page': items_per_page,
            'total_items': paginator.count,
            'start_index': assignments_page.start_index(),
            'end_index': assignments_page.end_index(),
        }
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
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Estadísticas del usuario
        total_solutions = UserSolutionAssignment.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        favorite_count = UserFavoriteSolution.objects.filter(
            user=request.user
        ).count()
        
        # Accesos recientes
        recent_accesses = UserSolutionAccess.objects.filter(
            user=request.user
        ).count()
        
        # Días desde el registro
        if request.user.created_at:
            days_active = (timezone.now() - request.user.created_at).days
        else:
            days_active = 0
        
        # Último acceso
        last_access = UserSolutionAccess.objects.filter(
            user=request.user
        ).order_by('-accessed_at').first()
        
        context = {
            'user': request.user,
            'page_title': 'Mi Perfil',
            'profile_stats': {
                'total_solutions': total_solutions,
                'favorite_count': favorite_count,
                'recent_accesses': recent_accesses,
                'days_active': days_active,
                'last_access': last_access,
            }
        }
        
        return render(request, 'dashboard/user_profile.html', context)
        
    except Exception as e:
        logger.error(f'Error en user_profile_view: {str(e)}')
        messages.error(request, 'Error al cargar el perfil')
        return redirect('user_dashboard')