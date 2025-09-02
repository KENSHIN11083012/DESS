"""
Implementación concreta de UserRepository usando Django ORM
"""
from typing import List, Optional
from core.interfaces.repositories import UserRepository
from core.entities.user import User, UserRole
from infrastructure.database.models import DESSUser
import logging

logger = logging.getLogger(__name__)


class DjangoUserRepository(UserRepository):
    """
    Implementación de UserRepository usando Django ORM.
    Convierte entre entidades de dominio y modelos Django.
    """
    
    def save(self, user: User) -> User:
        """Guardar usuario (crear o actualizar)"""
        try:
            if user.id:
                # Actualizar usuario existente
                django_user = DESSUser.objects.get(id=user.id)
                self._update_django_user_from_entity(django_user, user)
            else:
                # Crear nuevo usuario
                django_user = self._create_django_user_from_entity(user)
            
            django_user.save()
            return self._convert_to_entity(django_user)
            
        except Exception as e:
            logger.error(f"Error saving user: {str(e)}")
            raise
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuario por ID"""
        try:
            django_user = DESSUser.objects.get(id=user_id)
            return self._convert_to_entity(django_user)
        except DESSUser.DoesNotExist:
            return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Buscar usuario por nombre de usuario"""
        try:
            django_user = DESSUser.objects.get(username=username)
            return self._convert_to_entity(django_user)
        except DESSUser.DoesNotExist:
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email"""
        try:
            django_user = DESSUser.objects.get(email=email)
            return self._convert_to_entity(django_user)
        except DESSUser.DoesNotExist:
            return None
    
    def find_all(self) -> List[User]:
        """Obtener todos los usuarios"""
        django_users = DESSUser.objects.all()
        return [self._convert_to_entity(du) for du in django_users]
    
    def find_by_role(self, role: UserRole) -> List[User]:
        """Buscar usuarios por rol"""
        django_users = DESSUser.objects.filter(role=role.value)
        return [self._convert_to_entity(du) for du in django_users]
    
    def delete(self, user_id: int) -> bool:
        """Eliminar usuario por ID"""
        try:
            user = DESSUser.objects.get(id=user_id)
            user.delete()
            return True
        except DESSUser.DoesNotExist:
            return False
    
    def exists_by_username(self, username: str) -> bool:
        """Verificar si existe un usuario con este username"""
        return DESSUser.objects.filter(username=username).exists()
    
    def exists_by_email(self, email: str) -> bool:
        """Verificar si existe un usuario con este email"""
        return DESSUser.objects.filter(email=email).exists()
    
    def count_total(self) -> int:
        """Contar total de usuarios"""
        return DESSUser.objects.count()
    
    def count_active(self) -> int:
        """Contar usuarios activos"""
        return DESSUser.objects.filter(is_active=True).count()
    
    def _convert_to_entity(self, django_user: DESSUser) -> User:
        """Convertir modelo Django a entidad de dominio"""
        return User(
            id=django_user.id,
            username=django_user.username,
            email=django_user.email,
            full_name=django_user.full_name,
            role=UserRole(django_user.role),
            password=None,  # No exponemos password en la entidad
            is_active=django_user.is_active,
            created_at=django_user.created_at,
            updated_at=django_user.updated_at
        )
    
    def _create_django_user_from_entity(self, user: User) -> DESSUser:
        """Crear modelo Django desde entidad de dominio"""
        django_user = DESSUser(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active
        )
        
        if user.password:
            django_user.set_password(user.password)
            
        return django_user
    
    def _update_django_user_from_entity(self, django_user: DESSUser, user: User) -> None:
        """Actualizar modelo Django desde entidad de dominio"""
        django_user.username = user.username
        django_user.email = user.email
        django_user.full_name = user.full_name
        django_user.role = user.role.value
        django_user.is_active = user.is_active
        
        if user.password:
            django_user.set_password(user.password)