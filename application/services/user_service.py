"""
Servicio de aplicación para operaciones de usuario.
"""
from typing import Optional

from core.entities.user import User
from core.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    ListUsersUseCase,
    GetUserStatsUseCase
)
from core.interfaces.repositories import UserRepository
from application.dtos import CreateUserRequest, UserResponse, UserStatsResponse, UserListResponse


class UserService:
    """Servicio de aplicación para operaciones de usuario."""
    
    def __init__(self, 
                 create_user_use_case: CreateUserUseCase,
                 get_user_use_case: GetUserUseCase,
                 update_user_use_case: UpdateUserUseCase,
                 delete_user_use_case: DeleteUserUseCase,
                 list_users_use_case: ListUsersUseCase,
                 get_user_stats_use_case: GetUserStatsUseCase):
        """Inicializar servicio con casos de uso inyectados."""
        self.create_user_use_case = create_user_use_case
        self.get_user_use_case = get_user_use_case
        self.update_user_use_case = update_user_use_case
        self.delete_user_use_case = delete_user_use_case
        self.list_users_use_case = list_users_use_case
        self.get_user_stats_use_case = get_user_stats_use_case
    
    def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Crear un nuevo usuario."""
        # Usar caso de uso para crear usuario
        user = self.create_user_use_case.execute(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            role=request.role,
            password=request.password,
            is_active=request.is_active
        )        
        return self._user_to_response(user)
    
    def get_user(self, user_id: int) -> Optional[UserResponse]:
        """Obtener un usuario por ID."""
        user = self.get_user_use_case.execute(user_id)
        return self._user_to_response(user) if user else None
    
    def list_users(self, page: int = 1, page_size: int = 10) -> UserListResponse:
        """Listar usuarios."""
        users, total_count = self.list_users_use_case.execute(page=page, page_size=page_size)
        
        user_responses = [self._user_to_response(user) for user in users]
        total_pages = (total_count + page_size - 1) // page_size
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_user_stats(self) -> UserStatsResponse:
        """Obtener estadísticas de usuarios."""
        stats = self.get_user_stats_use_case.execute()
        
        return UserStatsResponse(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            inactive_users=stats['inactive_users'],
            super_admins=stats['super_admins'],
            regular_users=stats['regular_users']
        )
    
    def _user_to_response(self, user: User) -> UserResponse:
        """Convertir entidad User a UserResponse DTO."""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
