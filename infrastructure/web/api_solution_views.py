"""
API Views para operaciones de solución usando Clean Architecture.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from infrastructure.dependency_setup import get_solution_service
from application.dtos import (
    CreateSolutionRequest,
    UpdateSolutionRequest,
    AssignSolutionRequest,
    DeploySolutionRequest,
)
from .utils import (
    create_api_response,
    handle_api_exception,
    serialize_solution_data,
    create_pagination_data,
    validate_pagination_params
)


@api_view(['GET'])
def solution_list(request):
    """
    GET /api/v1/solutions/
    Listar soluciones con paginación y filtros.
    """
    try:
        solution_service = get_solution_service()
        
        # Parámetros de consulta
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        type_filter = request.GET.get('type')
        status_filter = request.GET.get('status')
        active_filter = request.GET.get('active')
        
        # Convertir active_filter a boolean si está presente
        if active_filter is not None:
            active_filter = active_filter.lower() == 'true'
        
        # Llamar al servicio
        result = solution_service.list_solutions(
            page=page,
            page_size=page_size,
            type_filter=type_filter,
            status_filter=status_filter,
            active_filter=active_filter
        )
        
        # Convertir DTOs a diccionarios para JSON
        solutions_data = []
        for solution in result.solutions:
            solutions_data.append({
                'id': solution.id,
                'name': solution.name,
                'description': solution.description,
                'repository_url': solution.repository_url,
                'solution_type': solution.solution_type,
                'status': solution.status,
                'access_url': solution.access_url,
                'version': solution.version,
                'created_at': solution.created_at.isoformat(),
                'updated_at': solution.updated_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'data': {
                'solutions': solutions_data,
                'pagination': {
                    'page': result.page,
                    'page_size': result.page_size,
                    'total_count': result.total_count,
                    'total_pages': result.total_pages,
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def solution_detail(request, solution_id):
    """
    GET /api/v1/solutions/{id}/
    Obtener detalles de una solución específica.
    """
    try:
        solution_service = get_solution_service()
        
        solution = solution_service.get_solution(solution_id)
        
        if not solution:
            return Response({
                'success': False,
                'error': 'Solución no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'id': solution.id,
                'name': solution.name,
                'description': solution.description,
                'repository_url': solution.repository_url,
                'solution_type': solution.solution_type,
                'status': solution.status,
                'access_url': solution.access_url,
                'version': solution.version,
                'created_at': solution.created_at.isoformat(),
                'updated_at': solution.updated_at.isoformat(),
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def solution_create(request):
    """
    POST /api/v1/solutions/
    Crear una nueva solución.
    """
    try:
        solution_service = get_solution_service()
        
        # Validar datos requeridos
        required_fields = ['name', 'description', 'repository_url', 'solution_type']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'success': False,
                    'error': f'Campo requerido: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear DTO de solicitud
        create_request = CreateSolutionRequest(
            name=request.data['name'],
            description=request.data['description'],
            repository_url=request.data['repository_url'],
            solution_type=request.data['solution_type'],
            version=request.data.get('version', '1.0.0'),
            is_active=request.data.get('is_active', True)
        )
        
        # Crear solución
        created_solution = solution_service.create_solution(create_request)
        
        return Response({
            'success': True,
            'data': {
                'id': created_solution.id,
                'name': created_solution.name,
                'description': created_solution.description,
                'repository_url': created_solution.repository_url,
                'solution_type': created_solution.solution_type,
                'status': created_solution.status,
                'version': created_solution.version,
            },
            'message': 'Solución creada exitosamente'
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def solution_update(request, solution_id):
    """
    PUT /api/v1/solutions/{id}/
    Actualizar una solución existente.
    """
    try:
        solution_service = get_solution_service()
        
        # Verificar que la solución existe
        existing_solution = solution_service.get_solution(solution_id)
        if not existing_solution:
            return Response({
                'success': False,
                'error': 'Solución no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Crear DTO de actualización
        update_request = UpdateSolutionRequest(
            name=request.data.get('name'),
            description=request.data.get('description'),
            repository_url=request.data.get('repository_url'),
            version=request.data.get('version'),
            is_active=request.data.get('is_active')
        )
        
        # Actualizar solución
        updated_solution = solution_service.update_solution(solution_id, update_request)
        
        if not updated_solution:
            return Response({
                'success': False,
                'error': 'Error al actualizar solución'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': {
                'id': updated_solution.id,
                'name': updated_solution.name,
                'description': updated_solution.description,
                'repository_url': updated_solution.repository_url,
                'solution_type': updated_solution.solution_type,
                'status': updated_solution.status,
                'version': updated_solution.version,
            },
            'message': 'Solución actualizada exitosamente'
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def solution_delete(request, solution_id):
    """
    DELETE /api/v1/solutions/{id}/
    Eliminar una solución.
    """
    try:
        solution_service = get_solution_service()
        
        # Verificar que la solución existe
        existing_solution = solution_service.get_solution(solution_id)
        if not existing_solution:
            return Response({
                'success': False,
                'error': 'Solución no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Eliminar solución
        deleted = solution_service.delete_solution(solution_id)
        
        if deleted:
            return Response({
                'success': True,
                'message': 'Solución eliminada exitosamente'
            })
        else:
            return Response({
                'success': False,
                'error': 'Error al eliminar solución'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def solution_stats(request):
    """
    GET /api/v1/solutions/stats/
    Obtener estadísticas de soluciones.
    """
    try:
        solution_service = get_solution_service()
        
        stats = solution_service.get_solution_stats()
        
        return Response({
            'success': True,
            'data': {
                'total_solutions': stats.total_solutions,
                'active_solutions': stats.active_solutions,
                'inactive_solutions': stats.inactive_solutions,
                'deployed_solutions': stats.deployed_solutions,
                'pending_solutions': stats.pending_solutions,
                'failed_solutions': stats.failed_solutions,
                'by_type': stats.by_type,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def solution_assign(request):
    """
    POST /api/v1/solutions/assign/
    Asignar solución a usuario.
    """
    try:
        solution_service = get_solution_service()
        
        # Validar datos requeridos
        if 'solution_id' not in request.data or 'user_id' not in request.data:
            return Response({
                'success': False,
                'error': 'solution_id y user_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear DTO de asignación
        assign_request = AssignSolutionRequest(
            solution_id=request.data['solution_id'],
            user_id=request.data['user_id']
        )
        
        # Asignar solución
        assigned = solution_service.assign_solution_to_user(assign_request)
        
        if assigned:
            return Response({
                'success': True,
                'message': 'Solución asignada exitosamente'
            })
        else:
            return Response({
                'success': False,
                'error': 'Error al asignar solución'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def solution_unassign(request):
    """
    DELETE /api/v1/solutions/unassign/
    Desasignar solución de usuario.
    """
    try:
        solution_service = get_solution_service()
        
        # Validar datos requeridos
        if 'solution_id' not in request.data or 'user_id' not in request.data:
            return Response({
                'success': False,
                'error': 'solution_id y user_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Desasignar solución
        unassigned = solution_service.unassign_solution_from_user(
            request.data['solution_id'],
            request.data['user_id']
        )
        
        if unassigned:
            return Response({
                'success': True,
                'message': 'Solución desasignada exitosamente'
            })
        else:
            return Response({
                'success': False,
                'error': 'Error al desasignar solución'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_solutions(request, user_id):
    """
    GET /api/v1/users/{id}/solutions/
    Obtener soluciones asignadas a un usuario.
    """
    try:
        solution_service = get_solution_service()
        
        user_solutions_response = solution_service.get_user_solutions(user_id)
        
        # Convertir a formato JSON
        solutions_data = []
        for assignment in user_solutions_response.solutions:
            solutions_data.append({
                'assignment_id': assignment.id,
                'assigned_at': assignment.assigned_at.isoformat(),
                'is_active': assignment.is_active,
                'solution': {
                    'id': assignment.solution.id,
                    'name': assignment.solution.name,
                    'description': assignment.solution.description,
                    'solution_type': assignment.solution.solution_type,
                    'status': assignment.solution.status,
                    'access_url': assignment.solution.access_url,
                    'version': assignment.solution.version,
                }
            })
        
        return Response({
            'success': True,
            'data': {
                'user_id': user_solutions_response.user_id,
                'total_count': user_solutions_response.total_count,
                'solutions': solutions_data,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
