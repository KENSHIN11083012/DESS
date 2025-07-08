"""
User Use Cases - Lógica de negocio para operaciones de usuarios
"""
from typing import List, Optional
from core.entities.user import User, UserRole
from core.interfaces.repositories import UserRepository


class BaseUserUseCase:
    """Clase base para casos de uso de usuario"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def _get_user_or_raise(self, user_id: int) -> User:
        """Helper para obtener usuario o lanzar excepción si no existe"""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")
        return user


class CreateUserUseCase(BaseUserUseCase):
    """Caso de uso: Crear un nuevo usuario"""
    
    def execute(self, username: str, email: str, password: str, 
                full_name: str, role: str = "user", is_active: bool = True) -> User:
        """
        Ejecutar creación de usuario con validaciones de negocio
        """
        # Convertir string a enum
        user_role = UserRole.SUPER_ADMIN if role == "super_admin" else UserRole.USER
        
        # Validar que no exista el username
        if self.user_repository.exists_by_username(username):
            raise ValueError(f"El usuario '{username}' ya existe")
        
        # Validar que no exista el email
        if self.user_repository.exists_by_email(email):
            raise ValueError(f"El email '{email}' ya está en uso")
        
        # Crear entidad usuario (las validaciones se ejecutan automáticamente)
        user = User(
            id=None,
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=user_role,
            is_active=is_active
        )
        
        # Guardar y retornar
        return self.user_repository.save(user)


class GetUserUseCase(BaseUserUseCase):
    """Caso de uso: Obtener un usuario"""
    
    def execute_by_id(self, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        return self.user_repository.find_by_id(user_id)
    
    def execute_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        return self.user_repository.find_by_username(username)
    
    def execute_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return self.user_repository.find_by_email(email)


class UpdateUserUseCase(BaseUserUseCase):
    """Caso de uso: Actualizar un usuario"""
    
    def execute(self, user_id: int, **updates) -> User:
        """
        Actualizar usuario con validaciones
        """
        # Obtener usuario existente
        user = self._get_user_or_raise(user_id)
        
        # Validar cambios de username si se especifica
        if 'username' in updates and updates['username'] != user.username:
            if self.user_repository.exists_by_username(updates['username']):
                raise ValueError(f"El usuario '{updates['username']}' ya existe")
        
        # Validar cambios de email si se especifica
        if 'email' in updates and updates['email'] != user.email:
            if self.user_repository.exists_by_email(updates['email']):
                raise ValueError(f"El email '{updates['email']}' ya está en uso")
        
        # Aplicar actualizaciones
        if 'username' in updates:
            user.username = updates['username']
        if 'email' in updates:
            user.email = updates['email']
        if 'full_name' in updates:
            user.full_name = updates['full_name']
        if 'role' in updates:
            user.change_role(updates['role'])
        if 'is_active' in updates:
            if updates['is_active']:
                user.activate()
            else:
                user.deactivate()
        
        # Validar entidad actualizada
        user.validate()
        
        return self.user_repository.save(user)


class DeleteUserUseCase(BaseUserUseCase):
    """Caso de uso: Eliminar un usuario"""
    
    def execute(self, user_id: int) -> bool:
        """
        Eliminar usuario con validaciones de negocio
        """
        # Verificar que el usuario existe
        user = self._get_user_or_raise(user_id)
        
        # Regla de negocio: No eliminar si es el único super admin
        if user.is_super_admin():
            super_admins = self.user_repository.find_by_role(UserRole.SUPER_ADMIN)
            if len(super_admins) <= 1:
                raise ValueError("No se puede eliminar el único super administrador")
        
        return self.user_repository.delete(user_id)


class ListUsersUseCase(BaseUserUseCase):
    """Caso de uso: Listar usuarios"""
    
    def execute_all(self) -> List[User]:
        """Obtener todos los usuarios"""
        return self.user_repository.find_all()
    
    def execute_by_role(self, role: UserRole) -> List[User]:
        """Obtener usuarios por rol"""
        return self.user_repository.find_by_role(role)
    
    def execute_active_only(self) -> List[User]:
        """Obtener solo usuarios activos"""
        all_users = self.user_repository.find_all()
        return [user for user in all_users if user.is_active]


class GetUserStatsUseCase:
    """Caso de uso: Obtener estadísticas de usuarios"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def execute(self) -> dict:
        """Obtener estadísticas de usuarios"""
        total = self.user_repository.count_total()
        active = self.user_repository.count_active()
        
        all_users = self.user_repository.find_all()
        super_admins = len([u for u in all_users if u.is_super_admin()])
        regular_users = len([u for u in all_users if not u.is_super_admin()])
        
        return {
            'total_users': total,
            'active_users': active,
            'inactive_users': total - active,
            'super_admins': super_admins,
            'regular_users': regular_users
        }
