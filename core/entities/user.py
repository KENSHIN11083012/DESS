"""
User Entity - Entidad de dominio para usuarios
Contiene la lógica de negocio pura sin dependencias externas
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime
import re
from core.constants import ValidationConstants


class UserRole(Enum):
    """Roles de usuario en el sistema DESS"""
    SUPER_ADMIN = "super_admin"
    USER = "user"


@dataclass
class User:
    """
    Entidad de dominio User.
    
    Representa un usuario del sistema DESS con toda su lógica de negocio.
    No tiene dependencias de frameworks externos.
    """
    id: Optional[int]
    username: str
    email: str
    full_name: str
    role: UserRole
    password: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        self.validate()
    
    def validate(self):
        """Validar la entidad según reglas de negocio"""
        self._validate_username()
        self._validate_email()
        self._validate_full_name()
        self._validate_password()
        self._validate_role()
    
    def _validate_username(self):
        """Validar nombre de usuario"""
        if not self.username:
            raise ValueError("El nombre de usuario es obligatorio")
        
        if len(self.username) < ValidationConstants.MIN_USERNAME_LENGTH:
            raise ValueError(f"El nombre de usuario debe tener al menos {ValidationConstants.MIN_USERNAME_LENGTH} caracteres")
        
        if len(self.username) > ValidationConstants.MAX_USERNAME_LENGTH:
            raise ValueError(f"El nombre de usuario no puede tener más de {ValidationConstants.MAX_USERNAME_LENGTH} caracteres")
        
        # Solo letras, números, guiones, guiones bajos y puntos
        if not re.match(ValidationConstants.USERNAME_REGEX, self.username):
            raise ValueError(ValidationConstants.USERNAME_PATTERN_MESSAGE)
    
    def _validate_email(self):
        """Validar formato de email"""
        if not self.email:
            raise ValueError("El email es obligatorio")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("El formato del email no es válido")
    
    def _validate_full_name(self):
        """Validar nombre completo"""
        if not self.full_name:
            raise ValueError("El nombre completo es obligatorio")
        
        if len(self.full_name.strip()) < ValidationConstants.MIN_FULL_NAME_LENGTH:
            raise ValueError(f"El nombre completo debe tener al menos {ValidationConstants.MIN_FULL_NAME_LENGTH} caracteres")
        
        if len(self.full_name) > ValidationConstants.MAX_FULL_NAME_LENGTH:
            raise ValueError(f"El nombre completo no puede tener más de {ValidationConstants.MAX_FULL_NAME_LENGTH} caracteres")
    
    def _validate_password(self):
        """Validar contraseña"""
        # Solo validar si se proporciona una contraseña
        if self.password is not None:
            if not self.password:
                raise ValueError("La contraseña es obligatoria")
            
            if len(self.password) < ValidationConstants.MIN_PASSWORD_LENGTH:
                raise ValueError(f"La contraseña debe tener al menos {ValidationConstants.MIN_PASSWORD_LENGTH} caracteres")
    
    def _validate_role(self):
        """Validar rol de usuario"""
        if not isinstance(self.role, UserRole):
            raise ValueError("El rol debe ser una instancia de UserRole")
    
    def validate_for_creation(self):
        """Validar entidad para operaciones de creación (requiere contraseña)"""
        if self.password is None or not self.password:
            raise ValueError("La contraseña es obligatoria")
        
        # Ejecutar todas las demás validaciones
        self.validate()
    
    def is_super_admin(self) -> bool:
        """Verificar si el usuario es super administrador"""
        return self.role == UserRole.SUPER_ADMIN
    
    def is_regular_user(self) -> bool:
        """Verificar si el usuario es usuario regular"""
        return self.role == UserRole.USER
    
    def activate(self):
        """Activar usuario"""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def deactivate(self):
        """Desactivar usuario"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def verify_password(self, password: str) -> bool:
        """Verificar si la contraseña es correcta"""
        # En un sistema real, aquí se verificaría el hash
        # Por simplicidad, comparación directa
        return self.password == password
    
    def change_password(self, new_password: str):
        """Cambiar contraseña del usuario"""
        old_password = self.password
        self.password = new_password
        try:
            self._validate_password()
            self.updated_at = datetime.now()
        except ValueError:
            # Revertir si la nueva contraseña no es válida
            self.password = old_password
            raise
    
    def change_role(self, new_role: str):
        """Cambiar rol del usuario"""
        old_role = self.role
        try:
            if new_role == "super_admin":
                self.role = UserRole.SUPER_ADMIN
            elif new_role == "user":
                self.role = UserRole.USER
            else:
                raise ValueError(f"Rol '{new_role}' no válido")
            
            self._validate_role()
            self.updated_at = datetime.now()
        except ValueError:
            self.role = old_role
            raise
    
    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None):
        """Actualizar perfil del usuario"""
        if full_name is not None:
            old_full_name = self.full_name
            self.full_name = full_name
            try:
                self._validate_full_name()
            except ValueError:
                self.full_name = old_full_name
                raise
        
        if email is not None:
            old_email = self.email
            self.email = email
            try:
                self._validate_email()
            except ValueError:
                self.email = old_email
                raise
        
        if full_name is not None or email is not None:
            self.updated_at = datetime.now()
    
    def can_manage_users(self) -> bool:
        """Verificar si el usuario puede gestionar otros usuarios"""
        return self.is_super_admin() and self.is_active
    
    def can_manage_solutions(self) -> bool:
        """Verificar si el usuario puede gestionar soluciones"""
        return self.is_super_admin() and self.is_active
    
    def can_access_solution(self, solution_id: int) -> bool:
        """Verificar si el usuario puede acceder a una solución específica"""
        # Los super admins pueden acceder a todas las soluciones
        if self.is_super_admin():
            return self.is_active
        
        # Los usuarios regulares solo pueden acceder si tienen asignación
        # Esta lógica se implementará en los casos de uso
        return self.is_active
    
    def __str__(self) -> str:
        """Representación string del usuario"""
        return f"User(username='{self.username}', email='{self.email}', role='{self.role.value}')"
    
    def __eq__(self, other) -> bool:
        """Comparación de igualdad basada en ID"""
        if not isinstance(other, User):
            return False
        
        # Si ambos tienen ID, comparar por ID
        if self.id is not None and other.id is not None:
            return self.id == other.id
        
        # Si no tienen ID, comparar por username (único)
        return self.username == other.username
    
    def __hash__(self) -> int:
        """Hash basado en ID o username"""
        if self.id is not None:
            return hash(self.id)
        return hash(self.username)
