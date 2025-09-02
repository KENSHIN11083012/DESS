"""
Implementación concreta de SolutionAssignmentRepository usando Django ORM
"""
from typing import List
from core.interfaces.repositories import SolutionAssignmentRepository
from infrastructure.database.models import UserSolutionAssignment, DESSUser, Solution
import logging

logger = logging.getLogger(__name__)


class DjangoSolutionAssignmentRepository(SolutionAssignmentRepository):
    """
    Implementación de SolutionAssignmentRepository usando Django ORM.
    Gestiona las relaciones entre usuarios y soluciones.
    """
    
    def assign_solution_to_user(self, user_id: int, solution_id: int) -> bool:
        """Asignar solución a usuario"""
        try:
            user = DESSUser.objects.get(id=user_id)
            solution = Solution.objects.get(id=solution_id)
            
            # Crear o reactivar asignación
            assignment, created = UserSolutionAssignment.objects.get_or_create(
                user=user,
                solution=solution,
                defaults={'is_active': True}
            )
            
            if not created and not assignment.is_active:
                assignment.is_active = True
                assignment.save()
            
            return True
            
        except (DESSUser.DoesNotExist, Solution.DoesNotExist) as e:
            logger.error(f"Error assigning solution: {str(e)}")
            return False
    
    def unassign_solution_from_user(self, user_id: int, solution_id: int) -> bool:
        """Desasignar solución de usuario"""
        try:
            assignment = UserSolutionAssignment.objects.get(
                user_id=user_id,
                solution_id=solution_id,
                is_active=True
            )
            assignment.is_active = False
            assignment.save()
            return True
            
        except UserSolutionAssignment.DoesNotExist:
            return False
    
    def is_solution_assigned_to_user(self, user_id: int, solution_id: int) -> bool:
        """Verificar si solución está asignada a usuario"""
        return UserSolutionAssignment.objects.filter(
            user_id=user_id,
            solution_id=solution_id,
            is_active=True
        ).exists()
    
    def get_user_solutions(self, user_id: int) -> List[int]:
        """Obtener IDs de soluciones asignadas a usuario"""
        return list(
            UserSolutionAssignment.objects.filter(
                user_id=user_id,
                is_active=True
            ).values_list('solution_id', flat=True)
        )
    
    def get_solution_users(self, solution_id: int) -> List[int]:
        """Obtener IDs de usuarios asignados a solución"""
        return list(
            UserSolutionAssignment.objects.filter(
                solution_id=solution_id,
                is_active=True
            ).values_list('user_id', flat=True)
        )
    
    def get_all_assignments(self) -> List[tuple]:
        """Obtener todas las asignaciones como tuplas (user_id, solution_id)"""
        assignments = UserSolutionAssignment.objects.filter(
            is_active=True
        ).values_list('user_id', 'solution_id')
        
        return list(assignments)
    
    def remove_all_user_assignments(self, user_id: int) -> int:
        """Remover todas las asignaciones de un usuario"""
        updated = UserSolutionAssignment.objects.filter(
            user_id=user_id,
            is_active=True
        ).update(is_active=False)
        
        return updated
    
    def remove_all_solution_assignments(self, solution_id: int) -> int:
        """Remover todas las asignaciones de una solución"""
        updated = UserSolutionAssignment.objects.filter(
            solution_id=solution_id,
            is_active=True
        ).update(is_active=False)
        
        return updated