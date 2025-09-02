"""
Vistas CRUD de Administrador - DESS
Responsable de operaciones de creación, edición y asignación
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment
from infrastructure.security.permissions import super_admin_required
from infrastructure.validation.decorators import validate_user_creation, validate_solution_creation, sanitize_input
from infrastructure.validation.validators import UserValidator, SolutionValidator, AssignmentValidator

logger = logging.getLogger(__name__)


@super_admin_required
@validate_user_creation
@sanitize_input(
    fields=['username', 'email', 'full_name'], 
    html_fields=['full_name'],
    max_lengths={'username': 30, 'email': 254, 'full_name': 100}
)
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
            access_url = request.POST.get('access_url')
            
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
                access_url=access_url,
                status='active',
                created_by=request.user
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
            solution.access_url = request.POST.get('access_url', solution.access_url)
            solution.status = request.POST.get('status', solution.status)
            solution.solution_type = request.POST.get('solution_type', solution.solution_type)
            solution.repository_url = request.POST.get('repository_url', solution.repository_url)
            solution.version = request.POST.get('version', solution.version)
            
            # Validaciones básicas
            if not solution.name or not solution.name.strip():
                raise ValueError("El nombre de la solución es obligatorio")
            
            if solution.status not in ['active', 'inactive', 'maintenance', 'error']:
                raise ValueError("Estado de solución inválido")
            
            solution.save()
            
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
            user_ids = request.POST.getlist('user_ids')
            
            if not user_ids:
                messages.error(request, 'Debes seleccionar al menos un usuario')
                return redirect('admin_assign_solution', solution_id=solution_id)
            
            assigned_count = 0
            for user_id in user_ids:
                user = get_object_or_404(DESSUser, id=user_id)
                
                # Verificar si ya está asignado
                assignment, created = UserSolutionAssignment.objects.get_or_create(
                    user=user,
                    solution=solution,
                    defaults={
                        'assigned_by': request.user,
                        'is_active': True
                    }
                )
                
                if created:
                    assigned_count += 1
                elif not assignment.is_active:
                    assignment.is_active = True
                    assignment.assigned_by = request.user
                    assignment.save()
                    assigned_count += 1
            
            if assigned_count > 0:
                messages.success(request, f'Solución asignada a {assigned_count} usuario(s) exitosamente')
            else:
                messages.info(request, 'Los usuarios seleccionados ya tenían asignada esta solución')
            
            return redirect('admin_solution_detail', solution_id=solution.id)
            
        except Exception as e:
            logger.error(f'Error assigning solution: {str(e)}')
            messages.error(request, 'Error al asignar la solución')
    
    # Obtener usuarios disponibles (que no tienen esta solución asignada)
    assigned_user_ids = UserSolutionAssignment.objects.filter(
        solution=solution,
        is_active=True
    ).values_list('user_id', flat=True)
    
    available_users = DESSUser.objects.exclude(
        id__in=assigned_user_ids
    ).filter(is_active=True).order_by('full_name')
    
    context = {
        'user': request.user,
        'solution': solution,
        'available_users': available_users,
        'page_title': f'Asignar: {solution.name}'
    }
    
    return render(request, 'dashboard/admin_assign_solution.html', context)


@super_admin_required
def design_system_view(request):
    """Vista para la documentación del sistema de diseño DESS"""
    context = {
        'user': request.user,
        'page_title': 'Sistema de Diseño DESS'
    }
    
    return render(request, 'dashboard/design_system.html', context)