"""
Implementación concreta de SolutionRepository usando Django ORM
"""
from typing import List, Optional
from core.interfaces.repositories import SolutionRepository
from core.entities.solution import Solution
from infrastructure.database.models import Solution as DjangoSolution
import logging

logger = logging.getLogger(__name__)


class DjangoSolutionRepository(SolutionRepository):
    """
    Implementación de SolutionRepository usando Django ORM.
    Convierte entre entidades de dominio y modelos Django.
    """
    
    def save(self, solution: Solution) -> Solution:
        """Guardar solución (crear o actualizar)"""
        try:
            if solution.id:
                # Actualizar solución existente
                django_solution = DjangoSolution.objects.get(id=solution.id)
                self._update_django_solution_from_entity(django_solution, solution)
            else:
                # Crear nueva solución
                django_solution = self._create_django_solution_from_entity(solution)
            
            django_solution.save()
            return self._convert_to_entity(django_solution)
            
        except Exception as e:
            logger.error(f"Error saving solution: {str(e)}")
            raise
    
    def find_by_id(self, solution_id: int) -> Optional[Solution]:
        """Buscar solución por ID"""
        try:
            django_solution = DjangoSolution.objects.get(id=solution_id)
            return self._convert_to_entity(django_solution)
        except DjangoSolution.DoesNotExist:
            return None
    
    def find_by_name(self, name: str) -> Optional[Solution]:
        """Buscar solución por nombre"""
        try:
            django_solution = DjangoSolution.objects.get(name=name)
            return self._convert_to_entity(django_solution)
        except DjangoSolution.DoesNotExist:
            return None
    
    def find_all(self) -> List[Solution]:
        """Obtener todas las soluciones"""
        django_solutions = DjangoSolution.objects.all()
        return [self._convert_to_entity(ds) for ds in django_solutions]
    
    def find_active(self) -> List[Solution]:
        """Obtener soluciones activas"""
        django_solutions = DjangoSolution.objects.filter(status='active')
        return [self._convert_to_entity(ds) for ds in django_solutions]
    
    def find_by_type(self, solution_type) -> List[Solution]:
        """Buscar soluciones por tipo"""
        django_solutions = DjangoSolution.objects.filter(solution_type=solution_type)
        return [self._convert_to_entity(ds) for ds in django_solutions]
    
    def delete(self, solution_id: int) -> bool:
        """Eliminar solución por ID"""
        try:
            solution = DjangoSolution.objects.get(id=solution_id)
            solution.delete()
            return True
        except DjangoSolution.DoesNotExist:
            return False
    
    def exists_by_name(self, name: str) -> bool:
        """Verificar si existe una solución con este nombre"""
        return DjangoSolution.objects.filter(name=name).exists()
    
    def count_total(self) -> int:
        """Contar total de soluciones"""
        return DjangoSolution.objects.count()
    
    def count_active(self) -> int:
        """Contar soluciones activas"""
        return DjangoSolution.objects.filter(status='active').count()
    
    def _convert_to_entity(self, django_solution: DjangoSolution) -> Solution:
        """Convertir modelo Django a entidad de dominio"""
        return Solution(
            id=django_solution.id,
            name=django_solution.name,
            description=django_solution.description,
            repository_url=django_solution.repository_url,
            solution_type=django_solution.solution_type,
            version=django_solution.version,
            access_url=django_solution.access_url,
            status=django_solution.status,
            created_at=django_solution.created_at,
            updated_at=django_solution.updated_at,
            created_by_id=django_solution.created_by.id if django_solution.created_by else None
        )
    
    def _create_django_solution_from_entity(self, solution: Solution) -> DjangoSolution:
        """Crear modelo Django desde entidad de dominio"""
        django_solution = DjangoSolution(
            name=solution.name,
            description=solution.description,
            repository_url=solution.repository_url,
            solution_type=solution.solution_type,
            version=solution.version,
            access_url=solution.access_url,
            status=solution.status
        )
        
        # Agregar created_by si existe
        if solution.created_by_id:
            from infrastructure.database.models import DESSUser
            try:
                created_by = DESSUser.objects.get(id=solution.created_by_id)
                django_solution.created_by = created_by
            except DESSUser.DoesNotExist:
                logger.warning(f"Created by user {solution.created_by_id} not found")
                
        return django_solution
    
    def _update_django_solution_from_entity(self, django_solution: DjangoSolution, solution: Solution) -> None:
        """Actualizar modelo Django desde entidad de dominio"""
        django_solution.name = solution.name
        django_solution.description = solution.description
        django_solution.repository_url = solution.repository_url
        django_solution.solution_type = solution.solution_type
        django_solution.version = solution.version
        django_solution.access_url = solution.access_url
        django_solution.status = solution.status