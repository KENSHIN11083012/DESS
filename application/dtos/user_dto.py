"""
DTOs para operaciones de usuario en la capa de aplicación.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class CreateUserRequest:
    """DTO para crear un nuevo usuario."""
    username: str
    email: str
    full_name: str
    password: str
    role: str = 'user'
    is_active: bool = True


@dataclass
class UpdateUserRequest:
    """DTO para actualizar un usuario existente."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass
class UserResponse:
    """DTO de respuesta para operaciones de usuario."""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class UserListResponse:
    """DTO para lista de usuarios con paginación."""
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


@dataclass
class UserStatsResponse:
    """DTO para estadísticas de usuarios."""
    total_users: int
    active_users: int
    inactive_users: int
    super_admins: int
    regular_users: int


@dataclass
class LoginRequest:
    """DTO para solicitud de login."""
    username: str
    password: str


@dataclass
class LoginResponse:
    """DTO para respuesta de login."""
    token: str
    user: UserResponse
    expires_in: int


@dataclass
class ChangePasswordRequest:
    """DTO para cambio de contraseña."""
    current_password: str
    new_password: str
