"""
Vistas del dashboard DESS refactorizadas
Eliminación de redundancias usando utilidades unificadas
"""
import logging
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess, UserFavoriteSolution
from infrastructure.security.permissions import (
    super_admin_required, 
    user_only_required, 
    ajax_login_required,
    ajax_super_admin_required,
    solution_access_required
)
from .utils import ListViewHelper, PermissionHelper, AuditHelper
from .dashboard_context import DashboardContextBuilder
import time

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
    """Dashboard principal para usuarios regulares"""
    try:
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        
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


@user_only_required
def user_solutions_view(request):
    """Vista de soluciones para usuarios regulares con filtrado"""
    from infrastructure.database.models import UserSolutionAssignment
    from django.db.models import Q
    
    # Obtener parámetros de filtrado
    search = request.GET.get('search', '').strip()
    solution_type = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    
    # Consulta base - soluciones asignadas al usuario
    assignments_query = UserSolutionAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('solution')
    
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
    
    # Obtener IDs de soluciones favoritas del usuario
    favorite_solution_ids = UserFavoriteSolution.objects.filter(
        user=request.user
    ).values_list('solution_id', flat=True)
    
    # Marcar cuáles son favoritas
    for assignment in assignments:
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
        'user_solutions': assignments,
        'solutions_stats': {
            'total_assigned': total_assigned,
            'ready_solutions': ready_solutions,      # Listas para usar
            'configuring_solutions': configuring_solutions,  # En configuración
            'maintenance_solutions': maintenance_solutions,   # En mantenimiento
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
            # Debug: registrar qué datos estamos recibiendo
            print("=== DEBUG CREATE SOLUTION ===")
            print("POST data:", dict(request.POST))
            print("access_url recibida:", request.POST.get('access_url'))
            print("=============================")
            
            # Obtener datos del formulario
            name = request.POST.get('name')
            description = request.POST.get('description')
            repository_url = request.POST.get('repository_url')
            solution_type = request.POST.get('solution_type')
            version = request.POST.get('version', '1.0.0')
            access_url = request.POST.get('access_url')  # ✅ AGREGADO
            
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
                access_url=access_url,  # ✅ AGREGADO
                status='active',
                created_by=request.user
            )
            
            # Debug: verificar después de crear
            print("=== DEBUG DESPUÉS DE CREATE ===")
            print("solution.access_url creada:", solution.access_url)
            print("===============================")
            
            # Registrar en auditoría
            # AuditHelper.log_admin_action(
            #     user=request.user,
            #     action='CREATE_SOLUTION',
            #     details=f'Solución creada: {solution.name}'
            # )
            
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
            # Debug: registrar qué datos estamos recibiendo
            print("=== DEBUG EDIT SOLUTION ===")
            print("POST data:", dict(request.POST))
            print("access_url recibida:", request.POST.get('access_url'))
            print("access_url antes de asignar:", solution.access_url)
            print("=============================")
            
            # Actualizar campos
            solution.name = request.POST.get('name', solution.name)
            solution.description = request.POST.get('description', solution.description)
            solution.access_url = request.POST.get('access_url', solution.access_url)
            solution.status = request.POST.get('status', solution.status)
            solution.solution_type = request.POST.get('solution_type', solution.solution_type)
            solution.repository_url = request.POST.get('repository_url', solution.repository_url)
            solution.version = request.POST.get('version', solution.version)
            
            # Debug: verificar valores antes del save
            print("=== DEBUG ANTES DEL SAVE ===")
            print("solution.access_url después de asignar:", solution.access_url)
            print("solution.name:", solution.name)
            print("solution.status:", solution.status)
            print("============================")
            
            # Validaciones básicas
            if not solution.name or not solution.name.strip():
                raise ValueError("El nombre de la solución es obligatorio")
            
            if solution.status not in ['active', 'inactive', 'maintenance', 'error']:
                raise ValueError("Estado de solución inválido")
            
            solution.save()
            
            # Debug: verificar después del save
            print("=== DEBUG DESPUÉS DEL SAVE ===")
            solution.refresh_from_db()
            print("solution.access_url después del save:", solution.access_url)
            print("==============================")
            
            # Registrar en auditoría (comentado temporalmente)
            # AuditHelper.log_admin_action(
            #     user=request.user,
            #     action='UPDATE_SOLUTION',
            #     details=f'Solución actualizada: {solution.name}'
            # )
            
            messages.success(request, f'Solución "{solution.name}" actualizada exitosamente')
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error updating solution: {str(e)}')
            context = {
                'user': request.user,
                'solution': solution,
                'page_title': f'Editar: {solution.name}',
                'error': str(e)
            }
            return render(request, 'dashboard/admin_edit_solution.html', context)
    
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
            # Debug: ver qué datos estamos recibiendo
            print("=== DEBUG ASSIGN SOLUTION ===")
            print("POST data:", request.POST)
            print("selected_users:", request.POST.getlist('selected_users'))
            print("user_ids:", request.POST.getlist('user_ids'))
            print("=============================")
            
            # Obtener IDs de usuarios seleccionados (puede venir como 'user_ids' o 'selected_users')
            user_ids = request.POST.getlist('selected_users') or request.POST.getlist('user_ids')
            
            if not user_ids:
                messages.warning(request, 'Debe seleccionar al menos un usuario')
                # Redirigir de vuelta al formulario
                return redirect('admin_assign_solution', solution_id=solution.id)
            
            # Asignar solución a usuarios seleccionados
            assigned_count = 0
            for user_id in user_ids:
                try:
                    user = DESSUser.objects.get(id=user_id)
                    assignment, created = UserSolutionAssignment.objects.get_or_create(
                        user=user,
                        solution=solution,
                        defaults={'assigned_by': request.user, 'is_active': True}
                    )
                    if created:
                        assigned_count += 1
                except DESSUser.DoesNotExist:
                    logger.warning(f'User with ID {user_id} not found')
                    continue
            
            # Registrar en auditoría
            # AuditHelper.log_admin_action(
            #     user=request.user,
            #     action='ASSIGN_SOLUTION',
            #     details=f'Solución {solution.name} asignada a {assigned_count} usuarios'
            # )
            
            if assigned_count > 0:
                messages.success(request, f'Solución asignada a {assigned_count} usuario(s) exitosamente')
            else:
                messages.info(request, 'No se realizaron nuevas asignaciones (usuarios ya tenían la solución asignada)')
            
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error assigning solution: {str(e)}')
            messages.error(request, f'Error al asignar la solución: {str(e)}')
    
    # Obtener usuarios asignados y disponibles
    assigned_users = UserSolutionAssignment.objects.filter(
        solution=solution,
        is_active=True
    ).select_related('user')
    
    assigned_user_ids = assigned_users.values_list('user_id', flat=True)
    
    available_users = DESSUser.objects.filter(
        role='user'
    ).exclude(
        id__in=assigned_user_ids
    ).order_by('first_name', 'last_name', 'username')
    
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


@ajax_super_admin_required
def api_delete_user(request):
    """API para eliminar un usuario"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        
        try:
            # Usar el servicio de usuario para eliminar
            from infrastructure.dependency_setup import get_user_service
            user_service = get_user_service()
            
            # Verificar que el usuario existe
            existing_user = user_service.get_user(user_id)
            if not existing_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no encontrado'
                }, status=404)
            
            # Verificar que no sea el usuario actual
            if int(user_id) == request.user.id:
                return JsonResponse({
                    'success': False,
                    'message': 'No puedes eliminar tu propia cuenta'
                }, status=400)
            
            # Eliminar usuario
            deleted = user_service.delete_user(int(user_id))
            
            if deleted:
                # Registrar en auditoría
                # AuditHelper.log_admin_action(
                #     user=request.user,
                #     action='DELETE_USER',
                #     details=f'Usuario eliminado: {existing_user.username}'
                # )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario "{existing_user.username}" eliminado exitosamente'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al eliminar usuario'
                }, status=500)
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'Error deleting user: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_super_admin_required
def api_delete_solution(request):
    """API para eliminar una solución"""
    if request.method == 'POST':
        solution_id = request.POST.get('solution_id')
        
        try:
            # Verificar que la solución existe
            solution = get_object_or_404(Solution, id=solution_id)
            
            # Obtener información antes de eliminar para logging
            solution_name = solution.name
            
            # Eliminar todas las asignaciones y accesos relacionados
            UserSolutionAssignment.objects.filter(solution=solution).delete()
            UserSolutionAccess.objects.filter(solution=solution).delete()
            
            # Eliminar la solución
            solution.delete()
            
            # Registrar en auditoría (comentado temporalmente)
            # AuditHelper.log_admin_action(
            #     user=request.user,
            #     action='DELETE_SOLUTION',
            #     details=f'Solución eliminada: {solution_name}'
            # )
            
            return JsonResponse({
                'success': True,
                'message': f'Solución "{solution_name}" eliminada exitosamente'
            })
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'Error deleting solution: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@login_required
@super_admin_required
def design_system_view(request):
    """Vista para la documentación del sistema de diseño DESS"""
    context = DashboardContextBuilder.build_admin_context(
        user=request.user,
        page_title='Sistema de Diseño DESS'
    )
    
    return render(request, 'dashboard/design_system.html', context)


@ajax_super_admin_required
def admin_stats_api(request):
    """
    API endpoint para obtener estadísticas del dashboard de administración
    """
    try:
        # Obtener estadísticas actualizadas
        total_users = DESSUser.objects.count()
        total_solutions = Solution.objects.count()
        total_assignments = UserSolutionAssignment.objects.count()
        
        # Estadísticas adicionales
        active_users = DESSUser.objects.filter(is_active=True).count()
        super_admins = DESSUser.objects.filter(role='super_admin').count()
        regular_users = DESSUser.objects.filter(role='user').count()
        
        # Estadísticas de soluciones
        active_solutions = Solution.objects.filter(status='active').count()
        
        stats = {
            'total_users': total_users,
            'total_solutions': total_solutions,
            'total_assignments': total_assignments,
            'active_users': active_users,
            'super_admins': super_admins,
            'regular_users': regular_users,
            'active_solutions': active_solutions,
            'timestamp': int(time.time())
        }
        
        logger.info(f"Estadísticas de admin solicitadas por {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de admin: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@ajax_login_required
def api_toggle_favorite(request):
    """API para alternar solución como favorita"""
    if request.method == 'POST':
        solution_id = request.POST.get('solution_id')
        
        try:
            # Verificar que la solución existe y el usuario tiene acceso
            solution = get_object_or_404(Solution, id=solution_id)
            
            # Verificar que el usuario tiene acceso a esta solución
            if not request.user.can_access_solution(solution_id):
                return JsonResponse({
                    'success': False,
                    'message': 'No tienes acceso a esta solución'
                }, status=403)
            
            # Alternar favorito
            favorite, created = UserFavoriteSolution.objects.get_or_create(
                user=request.user,
                solution=solution
            )
            
            if created:
                message = f'"{solution.name}" agregada a favoritos'
                is_favorite = True
            else:
                favorite.delete()
                message = f'"{solution.name}" removida de favoritos'
                is_favorite = False
            
            return JsonResponse({
                'success': True,
                'message': message,
                'is_favorite': is_favorite
            })
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'Error toggling favorite: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)
