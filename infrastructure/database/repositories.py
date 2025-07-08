"""
Implementaciones concretas de repositorios usando Django ORM.
"""
from typing import List, Optional, Dict, Any, Tuple
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model

from core.interfaces.repositories import (
    UserRepository,
    SolutionRepository,
    SolutionAssignmentRepository,
)
from core.entities.user import User, UserRole
from core.entities.solution import Solution, SolutionStatus, SolutionType
from infrastructure.database.models import DESSUser, Solution as SolutionModel, UserSolutionAssignment


class DjangoUserRepository(UserRepository):
    """Implementación concreta del repositorio de usuarios usando Django ORM."""
    
    def save(self, user: User) -> User:
        """Guardar usuario (crear o actualizar)."""
        if user.id:
            # Actualizar existente
            return self.update(user.id, {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
            })
        else:
            # Crear nuevo
            return self.create(user)
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuario por ID."""
        return self.get_by_id(user_id)
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Buscar usuario por nombre de usuario."""
        return self.get_by_username(username)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email."""
        return self.get_by_email(email)
    
    def find_all(self) -> List[User]:
        """Obtener todos los usuarios."""
        django_users = DESSUser.objects.all()
        return [self._django_user_to_entity(du) for du in django_users]
    
    def find_by_role(self, role: UserRole) -> List[User]:
        """Buscar usuarios por rol."""
        django_users = DESSUser.objects.filter(role=role.value)
        return [self._django_user_to_entity(du) for du in django_users]
    
    def exists_by_username(self, username: str) -> bool:
        """Verificar si existe un usuario con este username."""
        return DESSUser.objects.filter(username=username).exists()
    
    def exists_by_email(self, email: str) -> bool:
        """Verificar si existe un usuario con este email."""
        return DESSUser.objects.filter(email=email).exists()
    
    def count_total(self) -> int:
        """Contar total de usuarios."""
        return DESSUser.objects.count()
    
    def count_active(self) -> int:
        """Contar usuarios activos."""
        return DESSUser.objects.filter(is_active=True).count()
    
    # Métodos adicionales (no en la interfaz pero útiles)
    
    def create(self, user: User) -> User:
        """Crear un nuevo usuario."""
        # Validar que la contraseña exista
        if not user.password:
            raise ValueError("La contraseña es obligatoria")
            
        # Crear el usuario con todos los campos necesarios
        django_user = DESSUser.objects.create_user(
            username=user.username,
            email=user.email,
            password=user.password,  # Ahora siempre pasamos la contraseña
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
        )
        
        return self._django_user_to_entity(django_user)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtener usuario por ID."""
        try:
            django_user = DESSUser.objects.get(id=user_id)
            return self._django_user_to_entity(django_user)
        except ObjectDoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por nombre de usuario."""
        try:
            django_user = DESSUser.objects.get(username=username)
            return self._django_user_to_entity(django_user)
        except ObjectDoesNotExist:
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email."""
        try:
            django_user = DESSUser.objects.get(email=email)
            return self._django_user_to_entity(django_user)
        except ObjectDoesNotExist:
            return None
    
    def update(self, user_id: int, fields: Dict[str, Any]) -> Optional[User]:
        """Actualizar un usuario."""
        try:
            django_user = DESSUser.objects.get(id=user_id)
            
            for field, value in fields.items():
                if field == 'role' and isinstance(value, UserRole):
                    setattr(django_user, field, value.value)
                else:
                    setattr(django_user, field, value)
            
            django_user.save()
            return self._django_user_to_entity(django_user)
        except ObjectDoesNotExist:
            return None
    
    def delete(self, user_id: int) -> bool:
        """Eliminar un usuario."""
        try:
            django_user = DESSUser.objects.get(id=user_id)
            django_user.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def list(self, page: int = 1, page_size: int = 10, 
             role_filter: Optional[str] = None,
             active_filter: Optional[bool] = None) -> Tuple[List[User], int]:
        """Listar usuarios con paginación y filtros."""
        queryset = DESSUser.objects.all()
        
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        if active_filter is not None:
            queryset = queryset.filter(is_active=active_filter)
        
        total_count = queryset.count()
        
        # Paginación
        start = (page - 1) * page_size
        end = start + page_size
        django_users = queryset[start:end]
        
        users = [self._django_user_to_entity(django_user) for django_user in django_users]
        return users, total_count
    
    def get_stats(self) -> Dict[str, int]:
        """Obtener estadísticas de usuarios."""
        total_users = DESSUser.objects.count()
        active_users = DESSUser.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        super_admins = DESSUser.objects.filter(role='super_admin').count()
        regular_users = DESSUser.objects.filter(role='user').count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'super_admins': super_admins,
            'regular_users': regular_users,
        }
    
    def _django_user_to_entity(self, django_user: DESSUser) -> User:
        """Convertir modelo Django a entidad del dominio."""
        return User(
            id=django_user.id,
            username=django_user.username,
            email=django_user.email,
            full_name=django_user.full_name,
            role=UserRole(django_user.role),
            password=None,  # No exponemos la contraseña
            is_active=django_user.is_active,
            created_at=django_user.created_at,
            updated_at=django_user.updated_at,
        )


class DjangoSolutionRepository(SolutionRepository):
    """Implementación concreta del repositorio de soluciones usando Django ORM."""
    
    def save(self, solution: Solution) -> Solution:
        """Guardar solución (crear o actualizar)."""
        if solution.id:
            # Actualizar existente
            return self.update(solution.id, {
                'name': solution.name,
                'description': solution.description,
                'repository_url': solution.repository_url,
                'solution_type': solution.solution_type,
                'status': solution.status,
                'access_url': solution.access_url,
                'version': solution.version,
            })
        else:
            # Crear nuevo
            return self.create(solution)
    
    def find_by_id(self, solution_id: int) -> Optional[Solution]:
        """Buscar solución por ID."""
        return self.get_by_id(solution_id)
    
    def find_by_name(self, name: str) -> Optional[Solution]:
        """Buscar solución por nombre."""
        return self.get_by_name(name)
    
    def find_all(self) -> List[Solution]:
        """Obtener todas las soluciones."""
        django_solutions = SolutionModel.objects.all()
        return [self._django_solution_to_entity(ds) for ds in django_solutions]
    
    def find_active(self) -> List[Solution]:
        """Obtener soluciones activas."""
        django_solutions = SolutionModel.objects.filter(status='active')
        return [self._django_solution_to_entity(ds) for ds in django_solutions]
    
    def find_by_type(self, solution_type) -> List[Solution]:
        """Buscar soluciones por tipo."""
        type_value = solution_type.value if hasattr(solution_type, 'value') else solution_type
        return self.get_by_type(type_value)
    
    def exists_by_name(self, name: str) -> bool:
        """Verificar si existe una solución con este nombre."""
        return SolutionModel.objects.filter(name=name).exists()
    
    def count_total(self) -> int:
        """Contar total de soluciones."""
        return SolutionModel.objects.count()
    
    def count_active(self) -> int:
        """Contar soluciones activas."""
        return SolutionModel.objects.filter(status='active').count()
    
    # Métodos adicionales (no en la interfaz pero útiles)
    
    def create(self, solution: Solution) -> Solution:
        """Crear una nueva solución."""
        django_solution = SolutionModel.objects.create(
            name=solution.name,
            description=solution.description,
            repository_url=solution.repository_url,
            solution_type=solution.solution_type.value,
            status=solution.status.value,
            access_url=solution.access_url,
            version=solution.version,
        )
        
        return self._django_solution_to_entity(django_solution)
    
    def get_by_id(self, solution_id: int) -> Optional[Solution]:
        """Obtener solución por ID."""
        try:
            django_solution = SolutionModel.objects.get(id=solution_id)
            return self._django_solution_to_entity(django_solution)
        except ObjectDoesNotExist:
            return None
    
    def get_by_name(self, name: str) -> Optional[Solution]:
        """Obtener solución por nombre."""
        try:
            django_solution = SolutionModel.objects.get(name=name)
            return self._django_solution_to_entity(django_solution)
        except ObjectDoesNotExist:
            return None
    
    def get_by_type(self, solution_type: str) -> List[Solution]:
        """Obtener soluciones por tipo."""
        django_solutions = SolutionModel.objects.filter(solution_type=solution_type)
        return [self._django_solution_to_entity(ds) for ds in django_solutions]
    
    def get_by_status(self, status: str) -> List[Solution]:
        """Obtener soluciones por estado."""
        django_solutions = SolutionModel.objects.filter(status=status)
        return [self._django_solution_to_entity(ds) for ds in django_solutions]
    
    def update(self, solution_id: int, fields: Dict[str, Any]) -> Optional[Solution]:
        """Actualizar una solución."""
        try:
            django_solution = SolutionModel.objects.get(id=solution_id)
            
            for field, value in fields.items():
                if field == 'solution_type' and isinstance(value, SolutionType):
                    setattr(django_solution, field, value.value)
                elif field == 'status' and isinstance(value, SolutionStatus):
                    setattr(django_solution, field, value.value)
                else:
                    setattr(django_solution, field, value)
            
            django_solution.save()
            return self._django_solution_to_entity(django_solution)
        except ObjectDoesNotExist:
            return None
    
    def delete(self, solution_id: int) -> bool:
        """Eliminar una solución."""
        try:
            django_solution = SolutionModel.objects.get(id=solution_id)
            django_solution.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def list(self, page: int = 1, page_size: int = 10,
             type_filter: Optional[str] = None,
             status_filter: Optional[str] = None,
             active_filter: Optional[bool] = None) -> Tuple[List[Solution], int]:
        """Listar soluciones con paginación y filtros."""
        queryset = SolutionModel.objects.all()
        
        if type_filter:
            queryset = queryset.filter(solution_type=type_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        total_count = queryset.count()
        
        # Paginación
        start = (page - 1) * page_size
        end = start + page_size
        django_solutions = queryset[start:end]
        
        solutions = [self._django_solution_to_entity(ds) for ds in django_solutions]
        return solutions, total_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de soluciones."""
        total_solutions = SolutionModel.objects.count()
        active_solutions = SolutionModel.objects.filter(status='active').count()
        inactive_solutions = SolutionModel.objects.filter(status='inactive').count()
        deployed_solutions = SolutionModel.objects.exclude(access_url__isnull=True).count()
        pending_solutions = SolutionModel.objects.filter(access_url__isnull=True).count()
        failed_solutions = SolutionModel.objects.filter(status='error').count()
        
        # Estadísticas por tipo
        by_type = {}
        for choice in SolutionModel.TYPE_CHOICES:
            type_code = choice[0]
            count = SolutionModel.objects.filter(solution_type=type_code).count()
            by_type[type_code] = count
        
        return {
            'total_solutions': total_solutions,
            'active_solutions': active_solutions,
            'inactive_solutions': inactive_solutions,
            'deployed_solutions': deployed_solutions,
            'pending_solutions': pending_solutions,
            'failed_solutions': failed_solutions,
            'by_type': by_type,
        }
    
    def _django_solution_to_entity(self, django_solution: SolutionModel) -> Solution:
        """Convertir modelo Django a entidad del dominio."""
        return Solution(
            id=django_solution.id,
            name=django_solution.name,
            description=django_solution.description,
            repository_url=django_solution.repository_url,
            solution_type=SolutionType(django_solution.solution_type),
            status=SolutionStatus(django_solution.status),
            access_url=django_solution.access_url,
            version=django_solution.version,
            created_at=django_solution.created_at,
            updated_at=django_solution.updated_at,
        )


class DjangoSolutionAssignmentRepository(SolutionAssignmentRepository):
    """Implementación concreta del repositorio de asignaciones usando Django ORM."""
    
    def assign_solution_to_user(self, user_id: int, solution_id: int) -> bool:
        """Asignar solución a usuario."""
        return self.create(solution_id, user_id)
    
    def unassign_solution_from_user(self, user_id: int, solution_id: int) -> bool:
        """Desasignar solución de usuario."""
        return self.delete(solution_id, user_id)
    
    def is_solution_assigned_to_user(self, user_id: int, solution_id: int) -> bool:
        """Verificar si solución está asignada a usuario."""
        return self.exists(solution_id, user_id)
    
    def get_user_solutions(self, user_id: int) -> List[int]:
        """Obtener IDs de soluciones asignadas a usuario."""
        assignments = UserSolutionAssignment.objects.filter(
            user_id=user_id,
            is_active=True
        ).values_list('solution_id', flat=True)
        return list(assignments)
    
    def get_solution_users(self, solution_id: int) -> List[int]:
        """Obtener IDs de usuarios asignados a solución."""
        assignments = UserSolutionAssignment.objects.filter(
            solution_id=solution_id,
            is_active=True
        ).values_list('user_id', flat=True)
        return list(assignments)
    
    def get_all_assignments(self) -> List[tuple]:
        """Obtener todas las asignaciones como tuplas (user_id, solution_id)."""
        assignments = UserSolutionAssignment.objects.filter(
            is_active=True
        ).values_list('user_id', 'solution_id')
        return list(assignments)
    
    def remove_all_user_assignments(self, user_id: int) -> int:
        """Remover todas las asignaciones de un usuario."""
        count = UserSolutionAssignment.objects.filter(user_id=user_id).count()
        UserSolutionAssignment.objects.filter(user_id=user_id).delete()
        return count
    
    def remove_all_solution_assignments(self, solution_id: int) -> int:
        """Remover todas las asignaciones de una solución."""
        count = UserSolutionAssignment.objects.filter(solution_id=solution_id).count()
        UserSolutionAssignment.objects.filter(solution_id=solution_id).delete()
        return count
    
    # Métodos adicionales (mantenidos por compatibilidad)
    
    def create(self, solution_id: int, user_id: int, assigned_by_id: Optional[int] = None) -> bool:
        """Crear una nueva asignación."""
        try:
            with transaction.atomic():
                # Verificar que no exista ya la asignación
                if UserSolutionAssignment.objects.filter(
                    solution_id=solution_id,
                    user_id=user_id
                ).exists():
                    return False
                
                assignment = UserSolutionAssignment.objects.create(
                    solution_id=solution_id,
                    user_id=user_id,
                    assigned_by_id=assigned_by_id,
                    is_active=True
                )
                return True
        except Exception:
            return False
    
    def delete(self, solution_id: int, user_id: int) -> bool:
        """Eliminar una asignación."""
        try:
            assignment = UserSolutionAssignment.objects.get(
                solution_id=solution_id,
                user_id=user_id
            )
            assignment.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def get_user_assignments(self, user_id: int) -> List[Any]:
        """Obtener asignaciones de un usuario."""
        assignments = UserSolutionAssignment.objects.filter(
            user_id=user_id,
            is_active=True
        ).select_related('solution')
        
        return [
            {
                'id': assignment.id,
                'solution_id': assignment.solution_id,
                'user_id': assignment.user_id,
                'assigned_at': assignment.assigned_at,
                'is_active': assignment.is_active,
            }
            for assignment in assignments
        ]
    
    def get_solution_assignments(self, solution_id: int) -> List[Any]:
        """Obtener asignaciones de una solución."""
        assignments = UserSolutionAssignment.objects.filter(
            solution_id=solution_id,
            is_active=True
        ).select_related('user')
        
        return [
            {
                'id': assignment.id,
                'solution_id': assignment.solution_id,
                'user_id': assignment.user_id,
                'assigned_at': assignment.assigned_at,
                'is_active': assignment.is_active,
            }
            for assignment in assignments
        ]
    
    def exists(self, solution_id: int, user_id: int) -> bool:
        """Verificar si existe una asignación."""
        return UserSolutionAssignment.objects.filter(
            solution_id=solution_id,
            user_id=user_id,
            is_active=True
        ).exists()
