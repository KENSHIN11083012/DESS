"""
Utilidades unificadas para vistas DESS
Elimina redundancia en el manejo de contexto y validaciones
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess
from rest_framework import status
from rest_framework.response import Response
from typing import Any, Dict, Optional
import logging

from core.constants import APIConstants

logger = logging.getLogger(__name__)


class DashboardContextBuilder:
    """
    Constructor unificado de contexto para dashboards
    Elimina redundancia en la preparación de datos
    """
    
    def __init__(self, user):
        self.user = user
        self.context = {
            'user': user,
            'is_admin': user.is_super_admin()
        }
    
    def add_user_stats(self):
        """Agregar estadísticas del usuario actual"""
        if self.user.is_super_admin():
            # Stats para admin
            self.context.update({
                'stats': {
                    'total_users': DESSUser.objects.count(),
                    'regular_users': DESSUser.objects.filter(role='user').count(),
                    'super_admins': DESSUser.objects.filter(role='super_admin').count(),
                    'total_solutions': Solution.objects.count(),
                    'active_solutions': Solution.objects.filter(status='active').count(),
                    'inactive_solutions': Solution.objects.filter(status='inactive').count(),
                    'total_assignments': UserSolutionAssignment.objects.filter(is_active=True).count(),
                }
            })
        else:
            # Stats para usuario regular
            assigned_solutions = self.user.assigned_solutions.filter(
                usersolutionassignment__is_active=True
            )
            self.context.update({
                'assigned_solutions': assigned_solutions,
                'total_solutions': assigned_solutions.count(),
                'active_solutions': assigned_solutions.filter(status='active').count(),
            })
        
        return self
    
    def add_recent_activity(self, limit=10):
        """Agregar actividad reciente"""
        if self.user.is_super_admin():
            recent_assignments = UserSolutionAssignment.objects.select_related(
                'user', 'solution'
            ).order_by('-assigned_at')[:limit]
            self.context['recent_assignments'] = recent_assignments
        else:
            recent_accesses = UserSolutionAccess.objects.filter(
                user=self.user
            ).select_related('solution').order_by('-accessed_at')[:limit]
            self.context['recent_accesses'] = recent_accesses
        
        return self
    
    def add_solutions_data(self):
        """Agregar datos de soluciones"""
        if self.user.is_super_admin():
            # Admin ve todas las soluciones
            solutions = Solution.objects.annotate(
                users_count=Count('assigned_users')
            ).order_by('-created_at')
        else:
            # Usuario ve solo sus soluciones asignadas
            solutions = self.user.assigned_solutions.filter(
                usersolutionassignment__is_active=True
            ).order_by('name')
        
        self.context['solutions'] = solutions
        return self
    
    def build(self):
        """Construir y retornar el contexto final"""
        return self.context


class ListViewHelper:
    """
    Helper unificado para vistas de lista con filtros y paginación
    Elimina código repetitivo en vistas de gestión
    """
    
    def __init__(self, queryset, request, items_per_page=20):
        self.queryset = queryset
        self.request = request
        self.items_per_page = items_per_page
        self.filters = {}
    
    def add_search_filter(self, search_fields, param_name='search'):
        """Agregar filtro de búsqueda por texto"""
        search = self.request.GET.get(param_name, '').strip()
        if search:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": search})
            self.queryset = self.queryset.filter(q_objects)
            self.filters[param_name] = search
        return self
    
    def add_choice_filter(self, field_name, param_name=None):
        """Agregar filtro por campo de elección"""
        if param_name is None:
            param_name = field_name
        
        filter_value = self.request.GET.get(param_name, '').strip()
        if filter_value:
            self.queryset = self.queryset.filter(**{field_name: filter_value})
            self.filters[param_name] = filter_value
        return self
    
    def add_ordering(self, default_ordering='-created_at'):
        """Agregar ordenamiento"""
        ordering = self.request.GET.get('ordering', default_ordering)
        if ordering:
            self.queryset = self.queryset.order_by(ordering)
        return self
    
    def get_paginated_results(self):
        """Obtener resultados paginados"""
        page = self.request.GET.get('page', 1)
        paginator = Paginator(self.queryset, self.items_per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'items': page_obj,
            'filters': self.filters,
            'total_count': paginator.count
        }


class PermissionHelper:
    """
    Helper unificado para manejo de permisos
    Centraliza lógica de autorización
    """
    
    @staticmethod
    def can_access_admin_section(user):
        """Verificar si puede acceder a sección de admin"""
        return user.is_authenticated and user.is_super_admin()
    
    @staticmethod
    def can_access_user_section(user):
        """Verificar si puede acceder a sección de usuario"""
        return user.is_authenticated and not user.is_super_admin()
    
    @staticmethod
    def can_manage_user(admin_user, target_user):
        """Verificar si admin puede gestionar usuario"""
        return (admin_user.is_super_admin() and 
                admin_user != target_user)  # No puede gestionarse a sí mismo
    
    @staticmethod
    def can_access_solution(user, solution_id):
        """Verificar si usuario puede acceder a solución"""
        if user.is_super_admin():
            return True
        
        return user.assigned_solutions.filter(
            id=solution_id,
            usersolutionassignment__is_active=True,
            status='active'
        ).exists()
    
    @staticmethod
    def add_permission_error(request, message="No tienes permisos para realizar esta acción"):
        """Agregar mensaje de error de permisos"""
        messages.error(request, message)


class AuditHelper:
    """
    Helper para registro de auditoría
    Centraliza el logging de acciones
    """
    
    @staticmethod
    def log_solution_access(user, solution, ip_address=''):
        """Registrar acceso a solución"""
        return UserSolutionAccess.objects.create(
            user=user,
            solution=solution,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_user_assignment(admin_user, target_user, solution):
        """Registrar asignación de solución"""
        assignment, created = UserSolutionAssignment.objects.get_or_create(
            user=target_user,
            solution=solution,
            defaults={
                'assigned_by': admin_user,
                'is_active': True
            }
        )
        
        if not created and not assignment.is_active:
            # Reactivar asignación existente
            assignment.is_active = True
            assignment.assigned_by = admin_user
            assignment.save()
        
        return assignment, created


def create_api_response(
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """
    Crear respuesta API estandarizada.
    
    Args:
        success: Indica si la operación fue exitosa
        data: Datos de respuesta
        error: Mensaje de error si success=False
        status_code: Código de estado HTTP
    
    Returns:
        Response: Respuesta API estandarizada
    """
    response_data = {'success': success}
    
    if data is not None:
        response_data['data'] = data
    
    if error is not None:
        response_data['error'] = error
        
    return Response(response_data, status=status_code)


def handle_api_exception(e: Exception, default_message: str = "Error interno del servidor") -> Response:
    """
    Manejar excepciones de API de forma estandarizada.
    
    Args:
        e: Excepción capturada
        default_message: Mensaje por defecto si no se puede determinar el error
    
    Returns:
        Response: Respuesta de error estandarizada
    """
    logger.error(f"Error en API: {str(e)}", exc_info=True)
    
    # Determinar el tipo de error y el código de estado
    error_message = str(e) if str(e) else default_message
    
    # Mapear ciertos tipos de errores a códigos específicos
    if "no encontrado" in error_message.lower() or "not found" in error_message.lower():
        status_code = status.HTTP_404_NOT_FOUND
    elif "no autorizado" in error_message.lower() or "unauthorized" in error_message.lower():
        status_code = status.HTTP_401_UNAUTHORIZED
    elif "prohibido" in error_message.lower() or "forbidden" in error_message.lower():
        status_code = status.HTTP_403_FORBIDDEN
    elif "validación" in error_message.lower() or "validation" in error_message.lower():
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return create_api_response(
        success=False,
        error=error_message,
        status_code=status_code
    )


def serialize_user_data(user) -> Dict[str, Any]:
    """
    Serializar datos de usuario para respuesta API.
    
    Args:
        user: Objeto usuario
    
    Returns:
        Dict: Datos serializados del usuario
    """
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at),
        'updated_at': user.updated_at.isoformat() if hasattr(user.updated_at, 'isoformat') else str(user.updated_at),
    }


def serialize_solution_data(solution) -> Dict[str, Any]:
    """
    Serializar datos de solución para respuesta API.
    
    Args:
        solution: Objeto solución
    
    Returns:
        Dict: Datos serializados de la solución
    """
    return {
        'id': solution.id,
        'name': solution.name,
        'description': solution.description,
        'repository_url': solution.repository_url,
        'solution_type': solution.solution_type,
        'status': solution.status,
        'access_url': solution.access_url,
        'version': solution.version,
        'created_at': solution.created_at.isoformat() if hasattr(solution.created_at, 'isoformat') else str(solution.created_at),
        'updated_at': solution.updated_at.isoformat() if hasattr(solution.updated_at, 'isoformat') else str(solution.updated_at),
    }


def create_pagination_data(result) -> Dict[str, Any]:
    """
    Crear datos de paginación estandarizados.
    
    Args:
        result: Resultado con información de paginación
    
    Returns:
        Dict: Datos de paginación
    """
    return {
        'page': result.page,
        'page_size': result.page_size,
        'total_count': result.total_count,
        'total_pages': result.total_pages,
    }


def validate_pagination_params(request) -> Dict[str, Any]:
    """
    Validar y obtener parámetros de paginación de la request.
    
    Args:
        request: Request de Django
    
    Returns:
        Dict: Parámetros de paginación validados
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Validar rangos
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        elif page_size > APIConstants.MAX_RESULTS_PER_PAGE:  # Usar constante
            page_size = APIConstants.MAX_RESULTS_PER_PAGE
            
        return {
            'page': page,
            'page_size': page_size
        }
    except (ValueError, TypeError):
        return {
            'page': 1,
            'page_size': 10
        }
