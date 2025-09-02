"""
Casos de uso específicos para gestión de soluciones de usuario
"""
from typing import List, Optional
from core.interfaces.repositories import UserRepository, SolutionRepository, SolutionAssignmentRepository
from core.entities.user import User
from core.entities.solution import Solution
import logging

logger = logging.getLogger(__name__)


class GetUserSolutionsUseCase:
    """
    Caso de uso para obtener las soluciones asignadas a un usuario.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 solution_repository: SolutionRepository, 
                 assignment_repository: SolutionAssignmentRepository):
        self.user_repository = user_repository
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int) -> List[Solution]:
        """
        Obtener todas las soluciones asignadas a un usuario específico.
        """
        # Verificar que el usuario existe
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")
        
        # Obtener IDs de soluciones asignadas
        solution_ids = self.assignment_repository.get_user_solutions(user_id)
        
        # Obtener entidades completas de soluciones
        solutions = []
        for solution_id in solution_ids:
            solution = self.solution_repository.find_by_id(solution_id)
            if solution:
                solutions.append(solution)
            else:
                logger.warning(f"Solución con ID {solution_id} no encontrada")
        
        return solutions


class FilterUserSolutionsUseCase:
    """
    Caso de uso para filtrar soluciones de usuario según criterios.
    """
    
    def __init__(self, get_user_solutions_use_case: GetUserSolutionsUseCase):
        self.get_user_solutions_use_case = get_user_solutions_use_case
    
    def execute(self, 
                user_id: int, 
                search_term: Optional[str] = None,
                solution_type: Optional[str] = None,
                status: Optional[str] = None) -> List[Solution]:
        """
        Filtrar soluciones de usuario según criterios específicos.
        """
        # Obtener todas las soluciones del usuario
        solutions = self.get_user_solutions_use_case.execute(user_id)
        
        # Aplicar filtros
        filtered_solutions = solutions
        
        if search_term:
            search_term = search_term.lower()
            filtered_solutions = [
                s for s in filtered_solutions
                if (search_term in s.name.lower() or 
                    search_term in s.description.lower() or
                    search_term in s.version.lower())
            ]
        
        if solution_type:
            filtered_solutions = [
                s for s in filtered_solutions
                if s.solution_type == solution_type
            ]
        
        if status:
            filtered_solutions = [
                s for s in filtered_solutions
                if s.status == status
            ]
        
        return filtered_solutions


class AssignSolutionToUserUseCase:
    """
    Caso de uso para asignar una solución a un usuario.
    """
    
    def __init__(self,
                 user_repository: UserRepository,
                 solution_repository: SolutionRepository,
                 assignment_repository: SolutionAssignmentRepository):
        self.user_repository = user_repository
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int, solution_id: int) -> bool:
        """
        Asignar una solución específica a un usuario.
        """
        # Verificar que el usuario existe
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")
        
        # Verificar que la solución existe
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution:
            raise ValueError(f"Solución con ID {solution_id} no encontrada")
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise ValueError("No se puede asignar solución a usuario inactivo")
        
        # Verificar que la solución esté activa
        if solution.status != 'active':
            raise ValueError("No se puede asignar solución no activa")
        
        # Realizar la asignación
        success = self.assignment_repository.assign_solution_to_user(user_id, solution_id)
        
        if success:
            logger.info(f"Solución {solution_id} asignada a usuario {user_id}")
        else:
            logger.error(f"Error asignando solución {solution_id} a usuario {user_id}")
        
        return success


class UnassignSolutionFromUserUseCase:
    """
    Caso de uso para desasignar una solución de un usuario.
    """
    
    def __init__(self, assignment_repository: SolutionAssignmentRepository):
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int, solution_id: int) -> bool:
        """
        Desasignar una solución específica de un usuario.
        """
        # Verificar que la asignación existe
        is_assigned = self.assignment_repository.is_solution_assigned_to_user(user_id, solution_id)
        if not is_assigned:
            raise ValueError(f"Solución {solution_id} no está asignada a usuario {user_id}")
        
        # Realizar la desasignación
        success = self.assignment_repository.unassign_solution_from_user(user_id, solution_id)
        
        if success:
            logger.info(f"Solución {solution_id} desasignada de usuario {user_id}")
        else:
            logger.error(f"Error desasignando solución {solution_id} de usuario {user_id}")
        
        return success


class CheckSolutionAccessUseCase:
    """
    Caso de uso para verificar si un usuario puede acceder a una solución.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 solution_repository: SolutionRepository,
                 assignment_repository: SolutionAssignmentRepository):
        self.user_repository = user_repository
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int, solution_id: int) -> bool:
        """
        Verificar si un usuario puede acceder a una solución específica.
        """
        # Verificar que el usuario existe y está activo
        user = self.user_repository.find_by_id(user_id)
        if not user or not user.is_active:
            return False
        
        # Super admins pueden acceder a todo
        from core.entities.user import UserRole
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Verificar que la solución existe y está activa
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution or solution.status != 'active':
            return False
        
        # Verificar asignación
        return self.assignment_repository.is_solution_assigned_to_user(user_id, solution_id)