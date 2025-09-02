"""
Vistas de Administrador - DESS
Responsable de gestión de usuarios, soluciones y administración del sistema
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess
from infrastructure.security.permissions import super_admin_required
from ..utils import ListViewHelper, PermissionHelper, AuditHelper
from ..dashboard_context import DashboardContextBuilder

logger = logging.getLogger(__name__)


@super_admin_required
def admin_dashboard_view(request):
    """Vista del dashboard de administración para super administradores"""
    try:
        context_builder = DashboardContextBuilder(request.user)
        context = context_builder.add_user_stats().add_recent_activity().build()
        context['page_title'] = 'Panel de Administración'
        
        return render(request, 'dashboard/admin_dashboard.html', context)
    except Exception as e:
        logger.error(f'Error en admin_dashboard_view: {str(e)}')
        messages.error(request, 'Error al cargar el dashboard de administración')
        return redirect('login')


@super_admin_required
def admin_users_view(request):
    """Vista de gestión de usuarios para administradores"""
    # Usar helper de lista con queryset optimizado
    list_helper = ListViewHelper(
        queryset=DESSUser.objects.for_admin_dashboard(),
        request=request,
        items_per_page=20
    )
    
    results = (list_helper
               .add_search_filter(['username', 'full_name', 'email'])
               .add_choice_filter('role')
               .add_ordering('-date_joined')
               .get_paginated_results())
    
    context = {
        'user': request.user,
        'users': results['items'],
        'search': results['filters'].get('search', ''),
        'role_filter': results['filters'].get('role', ''),
        'total_count': results['total_count'],
        'page_title': 'Gestión de Usuarios'
    }
    
    return render(request, 'dashboard/admin_users.html', context)


@super_admin_required
def admin_solutions_view(request):
    """Vista de gestión de soluciones para administradores"""
    # Usar helper de lista con queryset optimizado
    list_helper = ListViewHelper(
        queryset=Solution.objects.for_admin_dashboard(),
        request=request,
        items_per_page=20
    )
    
    results = (list_helper
               .add_search_filter(['name', 'description'])
               .add_choice_filter('status')
               .add_ordering('-created_at')
               .get_paginated_results())
    
    context = {
        'user': request.user,
        'solutions': results['items'],
        'search': results['filters'].get('search', ''),
        'status_filter': results['filters'].get('status', ''),
        'total_count': results['total_count'],
        'page_title': 'Gestión de Soluciones'
    }
    
    return render(request, 'dashboard/admin_solutions.html', context)


@super_admin_required
def admin_user_detail_view(request, user_id):
    """Vista de detalle de usuario para administradores"""
    target_user = get_object_or_404(DESSUser, id=user_id)
    
    # Verificar permisos usando helper
    if not PermissionHelper.can_manage_user(request.user, target_user):
        PermissionHelper.add_permission_error(request)
        return redirect('admin_users')
    
    # Obtener datos del usuario con consultas optimizadas
    assignments = UserSolutionAssignment.objects.for_user(target_user).with_related_info().filter(
        user=target_user
    ).select_related('solution').order_by('-assigned_at')
    
    recent_accesses = UserSolutionAccess.objects.for_user(target_user).with_related_info().filter(
        user=target_user
    ).select_related('solution').order_by('-accessed_at')[:10]
    
    context = {
        'user': request.user,
        'target_user': target_user,
        'assignments': assignments,
        'recent_accesses': recent_accesses,
        'page_title': f'Usuario: {target_user.full_name}'
    }
    
    return render(request, 'dashboard/admin_user_detail.html', context)


@super_admin_required
def admin_solution_detail_view(request, solution_id):
    """Vista de detalle de solución para administradores"""
    solution = get_object_or_404(Solution, id=solution_id)
    
    # Obtener datos de la solución
    assignments = UserSolutionAssignment.objects.filter(
        solution=solution
    ).select_related('user').order_by('-assigned_at')
    
    access_stats = UserSolutionAccess.objects.filter(
        solution=solution
    ).select_related('user').order_by('-accessed_at')[:20]
    
    context = {
        'user': request.user,
        'solution': solution,
        'assignments': assignments,
        'access_stats': access_stats,
        'page_title': f'Solución: {solution.name}'
    }
    
    return render(request, 'dashboard/admin_solution_detail.html', context)