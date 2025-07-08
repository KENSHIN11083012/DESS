"""
Profile Use Cases - Lógica de negocio para operaciones de perfil de usuario
"""
from typing import Dict, Any, Optional
from datetime import datetime
from core.entities.user import User
from core.interfaces.repositories import UserRepository


class BaseProfileUseCase:
    """Clase base para casos de uso de perfil"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def _get_user_or_raise(self, user_id: int) -> User:
        """Helper para obtener usuario o lanzar excepción si no existe"""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")
        return user


class GetUserProfileUseCase(BaseProfileUseCase):
    """Caso de uso: Obtener perfil de usuario"""
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener perfil completo del usuario
        """
        user = self._get_user_or_raise(user_id)
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'last_login': getattr(user, 'last_login', None),
            'profile_completion': self._calculate_profile_completion(user),
            'permissions': self._get_user_permissions(user)
        }
    
    def _calculate_profile_completion(self, user: User) -> int:
        """Calcular porcentaje de completitud del perfil"""
        total_fields = 5
        completed_fields = 0
        
        if user.username:
            completed_fields += 1
        if user.email:
            completed_fields += 1
        if user.full_name:
            completed_fields += 1
        if user.role:
            completed_fields += 1
        if user.is_active:
            completed_fields += 1
            
        return int((completed_fields / total_fields) * 100)
    
    def _get_user_permissions(self, user: User) -> Dict[str, bool]:
        """Obtener permisos del usuario"""
        is_super_admin = user.is_super_admin()
        
        return {
            'can_manage_users': is_super_admin,
            'can_manage_solutions': is_super_admin,
            'can_view_dashboard': True,
            'can_edit_profile': True,
            'can_change_password': True,
            'can_view_logs': is_super_admin,
            'can_export_data': is_super_admin,
            'can_system_maintenance': is_super_admin
        }


class UpdateUserProfileUseCase(BaseProfileUseCase):
    """Caso de uso: Actualizar perfil de usuario"""
    
    def execute(self, user_id: int, updates: Dict[str, Any]) -> User:
        """
        Actualizar perfil de usuario con validaciones
        """
        user = self._get_user_or_raise(user_id)
        
        # Validar y aplicar solo campos permitidos para perfil
        allowed_fields = ['email', 'full_name']
        
        for field, value in updates.items():
            if field not in allowed_fields:
                continue
                
            if field == 'email' and value != user.email:
                if self.user_repository.exists_by_email(value):
                    raise ValueError(f"El email '{value}' ya está en uso")
                user.email = value
                
            elif field == 'full_name':
                user.full_name = value
        
        # Validar entidad actualizada
        user.validate()
        
        # Actualizar timestamp
        user.updated_at = datetime.now()
        
        return self.user_repository.save(user)


class ChangePasswordUseCase(BaseProfileUseCase):
    """Caso de uso: Cambiar contraseña"""
    
    def execute(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Cambiar contraseña del usuario
        """
        user = self._get_user_or_raise(user_id)
        
        # Verificar contraseña actual
        if not user.verify_password(current_password):
            raise ValueError("La contraseña actual es incorrecta")
        
        # Validar nueva contraseña
        if current_password == new_password:
            raise ValueError("La nueva contraseña debe ser diferente a la actual")
        
        # Cambiar contraseña
        user.change_password(new_password)
        
        # Actualizar timestamp
        user.updated_at = datetime.now()
        
        # Guardar cambios
        self.user_repository.save(user)
        
        return True


class GetUserActivityUseCase(BaseProfileUseCase):
    """Caso de uso: Obtener actividad del usuario"""
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener información de actividad del usuario
        """
        user = self._get_user_or_raise(user_id)
        
        # Simular datos de actividad (en un sistema real vendría de logs/auditoría)
        return {
            'last_login': getattr(user, 'last_login', None),
            'login_count': getattr(user, 'login_count', 0),
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'account_age_days': self._calculate_account_age(user),
            'status': 'active' if user.is_active else 'inactive'
        }
    
    def _calculate_account_age(self, user: User) -> int:
        """Calcular edad de la cuenta en días"""
        if not user.created_at:
            return 0
        
        delta = datetime.now() - user.created_at
        return delta.days


class ValidateUserDataUseCase(BaseProfileUseCase):
    """Caso de uso: Validar datos de usuario - Delega a entidades para evitar duplicación"""
    
    def execute_username(self, username: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Validar disponibilidad de username usando la lógica de la entidad"""
        try:
            # Crear usuario temporal para validar formato (usando lógica de entidad)
            from core.entities.user import User, UserRole
            temp_user = User(
                id=None,
                username=username,
                email="temp@temp.com",  # Email temporal válido
                full_name="Temp User",
                role=UserRole.USER,
                password="temppass123"  # Password temporal válido
            )
            # La validación se ejecuta automáticamente en __post_init__
            
        except ValueError as e:
            return {'valid': False, 'message': str(e)}
        
        # Verificar disponibilidad en repositorio
        existing_user = self.user_repository.find_by_username(username)
        if existing_user and (not user_id or existing_user.id != user_id):
            return {'valid': False, 'message': f"El nombre de usuario '{username}' ya está en uso"}
        
        return {'valid': True, 'message': 'Nombre de usuario disponible'}
    
    def execute_email(self, email: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Validar email usando la lógica de la entidad"""
        try:
            # Crear usuario temporal para validar formato (usando lógica de entidad)
            from core.entities.user import User, UserRole
            temp_user = User(
                id=None,
                username="tempuser",
                email=email,
                full_name="Temp User",
                role=UserRole.USER,
                password="temppass123"
            )
            # La validación se ejecuta automáticamente en __post_init__
            
        except ValueError as e:
            return {'valid': False, 'message': str(e)}
        
        # Verificar disponibilidad en repositorio
        existing_user = self.user_repository.find_by_email(email)
        if existing_user and (not user_id or existing_user.id != user_id):
            return {'valid': False, 'message': f"El email '{email}' ya está en uso"}
        
        return {'valid': True, 'message': 'Email válido'}
