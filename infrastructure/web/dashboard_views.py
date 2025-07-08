"""
Vistas del dashboard DESS refactorizadas
Eliminación de redundancias usando utilidades unificadas
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess
from infrastructure.security.permissions import (
    super_admin_required, 
    user_only_required, 
    ajax_login_required,
    ajax_super_admin_required,
    solution_access_required
)
from .utils import DashboardContextBuilder, ListViewHelper, PermissionHelper, AuditHelper

logger = logging.getLogger(__name__)


def login_view(request):
    """Vista de login personalizada para DESS"""
    if request.user.is_authenticated:
        # Redirigir según el rol del usuario
        if request.user.role == 'super_admin':
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    
    # Limpiar mensajes antiguos al acceder al login (GET)
    if request.method == 'GET':
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Esto consume y elimina los mensajes viejos
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.full_name}!')
            
            # Redirigir según el rol del usuario después del login
            if user.role == 'super_admin':
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard principal - redirige según el rol del usuario"""
    if request.user.role == 'super_admin':
        return redirect('admin_dashboard')
    else:
        return redirect('user_dashboard')


@user_only_required
def user_dashboard_view(request):
    """Dashboard para usuarios regulares - redirige a soluciones del usuario"""
    # En lugar de un dashboard separado, redirigimos a las soluciones del usuario
    return redirect('user_solutions')


@super_admin_required
def admin_dashboard_view(request):
    """Dashboard para super administradores"""
    context_builder = DashboardContextBuilder(request.user)
    context = context_builder.add_user_stats().add_recent_activity().build()
    context['page_title'] = 'Panel de Administración'
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@user_only_required
def user_solutions_view(request):
    """Vista de soluciones para usuarios regulares"""
    context_builder = DashboardContextBuilder(request.user)
    context = context_builder.add_solutions_data().build()
    context['page_title'] = 'Mis Soluciones'
    
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


@super_admin_required
def admin_users_view(request):
    """Vista de gestión de usuarios para administradores"""
    # Usar helper de lista para filtros y paginación
    list_helper = ListViewHelper(
        queryset=DESSUser.objects.all(),
        request=request,
        items_per_page=20
    )
    
    results = (list_helper
               .add_search_filter(['username', 'full_name', 'email'])
               .add_choice_filter('role')
               .add_ordering('-created_at')
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
    # Usar helper de lista para filtros y paginación
    list_helper = ListViewHelper(
        queryset=Solution.objects.all(),
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
    
    # Obtener datos del usuario
    assignments = UserSolutionAssignment.objects.filter(
        user=target_user
    ).select_related('solution').order_by('-assigned_at')
    
    recent_accesses = UserSolutionAccess.objects.filter(
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


@user_only_required
def user_profile_view(request):
    """Vista de perfil de usuario"""
    user = request.user
    
    # Obtener estadísticas del usuario
    total_solutions = user.assigned_solutions.filter(
        usersolutionassignment__is_active=True
    ).count()
    
    last_access = UserSolutionAccess.objects.filter(
        user=user
    ).order_by('-accessed_at').first()
    
    context = {
        'user': user,
        'total_solutions': total_solutions,
        'last_access': last_access,
        'page_title': 'Mi Perfil'
    }
    
    return render(request, 'dashboard/profile.html', context)


@super_admin_required
@super_admin_required
def admin_create_user_view(request):
    """Vista para crear un nuevo usuario"""
    # Limpiar mensajes antiguos al acceder a la página
    if request.method == 'GET':
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Esto consume y elimina los mensajes
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        role = request.POST.get('role', 'user')
        
        # Validaciones previas para asegurar que todos los campos estén completos
        if not (username and email and full_name and password):
            missing_fields = []
            if not username:
                missing_fields.append("Nombre de usuario")
            if not email:
                missing_fields.append("Email")
            if not full_name:
                missing_fields.append("Nombre completo")
            if not password:
                missing_fields.append("Contraseña")
                
            messages.error(request, f"Error: Los siguientes campos son obligatorios: {', '.join(missing_fields)}")
            return render(request, 'dashboard/admin_create_user.html', {'user': request.user, 'page_title': 'Crear Usuario'})
        
        try:
            from infrastructure.dependency_setup import get_user_service
            from application.dtos import CreateUserRequest
            user_service = get_user_service()
            
            user_request = CreateUserRequest(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                is_active=True
            )
            
            user = user_service.create_user(request=user_request)
            
            messages.success(request, f'Usuario {username} creado exitosamente')
            return redirect('admin_users')
            
        except ValueError as e:
            messages.error(request, f'Error de validación: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
    
    context = {
        'user': request.user,
        'page_title': 'Crear Usuario'
    }
    
    return render(request, 'dashboard/admin_create_user.html', context)


@super_admin_required
def admin_create_solution_view(request):
    """Vista para crear nueva solución"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.POST.get('name')
            description = request.POST.get('description')
            repository_url = request.POST.get('repository_url')
            solution_type = request.POST.get('solution_type')
            version = request.POST.get('version', '1.0.0')
            
            # Validar datos requeridos
            if not all([name, description, repository_url, solution_type]):
                messages.error(request, 'Todos los campos son requeridos')
                return render(request, 'dashboard/admin_create_solution.html', {
                    'user': request.user,
                    'page_title': 'Crear Nueva Solución'
                })
            
            # Crear la solución
            solution = Solution.objects.create(
                name=name,
                description=description,
                repository_url=repository_url,
                solution_type=solution_type,
                version=version,
                status='active',
                created_by=request.user
            )
            
            # Registrar en auditoría
            AuditHelper.log_admin_action(
                user=request.user,
                action='CREATE_SOLUTION',
                details=f'Solución creada: {solution.name}'
            )
            
            messages.success(request, f'Solución "{solution.name}" creada exitosamente')
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error creating solution: {str(e)}')
            messages.error(request, 'Error al crear la solución')
    
    context = {
        'user': request.user,
        'page_title': 'Crear Nueva Solución'
    }
    
    return render(request, 'dashboard/admin_create_solution.html', context)


@super_admin_required
def admin_edit_solution_view(request, solution_id):
    """Vista para editar solución existente"""
    solution = get_object_or_404(Solution, id=solution_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos
            solution.name = request.POST.get('name', solution.name)
            solution.description = request.POST.get('description', solution.description)
            solution.repository_url = request.POST.get('repository_url', solution.repository_url)
            solution.solution_type = request.POST.get('solution_type', solution.solution_type)
            solution.version = request.POST.get('version', solution.version)
            solution.access_url = request.POST.get('access_url', solution.access_url)
            
            solution.save()
            
            # Registrar en auditoría
            AuditHelper.log_admin_action(
                user=request.user,
                action='UPDATE_SOLUTION',
                details=f'Solución actualizada: {solution.name}'
            )
            
            messages.success(request, f'Solución "{solution.name}" actualizada exitosamente')
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error updating solution: {str(e)}')
            messages.error(request, 'Error al actualizar la solución')
    
    context = {
        'user': request.user,
        'solution': solution,
        'page_title': f'Editar: {solution.name}'
    }
    
    return render(request, 'dashboard/admin_edit_solution.html', context)


@super_admin_required
def admin_assign_solution_view(request, solution_id):
    """Vista para asignar solución a usuarios"""
    solution = get_object_or_404(Solution, id=solution_id)
    
    if request.method == 'POST':
        try:
            user_ids = request.POST.getlist('user_ids')
            
            # Asignar solución a usuarios seleccionados
            assigned_count = 0
            for user_id in user_ids:
                try:
                    user = DESSUser.objects.get(id=user_id)
                    assignment, created = UserSolutionAssignment.objects.get_or_create(
                        user=user,
                        solution=solution,
                        defaults={'assigned_by': request.user}
                    )
                    if created:
                        assigned_count += 1
                except DESSUser.DoesNotExist:
                    continue
            
            # Registrar en auditoría
            AuditHelper.log_admin_action(
                user=request.user,
                action='ASSIGN_SOLUTION',
                details=f'Solución {solution.name} asignada a {assigned_count} usuarios'
            )
            
            messages.success(request, f'Solución asignada a {assigned_count} usuarios exitosamente')
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error assigning solution: {str(e)}')
            messages.error(request, 'Error al asignar la solución')
    
    # Obtener usuarios disponibles y asignados
    assigned_users = UserSolutionAssignment.objects.filter(
        solution=solution
    ).select_related('user')
    
    available_users = DESSUser.objects.filter(
        role='user'
    ).exclude(
        id__in=assigned_users.values_list('user_id', flat=True)
    )
    
    context = {
        'user': request.user,
        'solution': solution,
        'assigned_users': assigned_users,
        'available_users': available_users,
        'page_title': f'Asignar: {solution.name}'
    }
    
    return render(request, 'dashboard/admin_assign_solution.html', context)


# === API VIEWS ===

@ajax_login_required
def api_user_profile(request):
    """API para obtener perfil del usuario"""
    user = request.user
    
    data = {
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'role': user.get_role_display(),
        'is_super_admin': user.is_super_admin(),
        'assigned_solutions_count': user.assigned_solutions.filter(
            usersolutionassignment__is_active=True
        ).count() if not user.is_super_admin() else 'ALL'
    }
    
    return JsonResponse(data)


@ajax_super_admin_required
def api_remove_assignment(request):
    """API para remover asignación de solución"""
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        try:
            assignment = UserSolutionAssignment.objects.get(id=assignment_id)
            assignment.is_active = False
            assignment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Asignación removida correctamente'
            })
        except UserSolutionAssignment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Asignación no encontrada'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)
