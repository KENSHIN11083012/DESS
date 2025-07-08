"""
Profile Service - Servicio de aplicación para perfil de usuario
Orquesta los casos de uso relacionados con perfil
"""
from typing import Dict, Any, Optional
from core.use_cases.profile_use_cases import (
    GetUserProfileUseCase,
    UpdateUserProfileUseCase,
    ChangePasswordUseCase,
    GetUserActivityUseCase,
    ValidateUserDataUseCase
)
from core.entities.user import User


class ProfileService:
    """Servicio para operaciones de perfil de usuario"""
    
    def __init__(self,
                 get_profile_use_case: GetUserProfileUseCase,
                 update_profile_use_case: UpdateUserProfileUseCase,
                 change_password_use_case: ChangePasswordUseCase,
                 get_activity_use_case: GetUserActivityUseCase,
                 validate_data_use_case: ValidateUserDataUseCase):
        self.get_profile_use_case = get_profile_use_case
        self.update_profile_use_case = update_profile_use_case
        self.change_password_use_case = change_password_use_case
        self.get_activity_use_case = get_activity_use_case
        self.validate_data_use_case = validate_data_use_case
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener perfil completo del usuario
        """
        try:
            return self.get_profile_use_case.execute(user_id)
        except Exception as e:
            raise Exception(f"Error al obtener perfil: {str(e)}")
    
    def update_profile(self, user_id: int, updates: Dict[str, Any]) -> User:
        """
        Actualizar perfil del usuario
        """
        try:
            # Validar datos antes de actualizar
            if 'email' in updates:
                validation = self.validate_data_use_case.execute_email(updates['email'], user_id)
                if not validation['valid']:
                    raise ValueError(validation['message'])
            
            return self.update_profile_use_case.execute(user_id, updates)
        except Exception as e:
            raise Exception(f"Error al actualizar perfil: {str(e)}")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Cambiar contraseña del usuario
        """
        try:
            return self.change_password_use_case.execute(user_id, current_password, new_password)
        except Exception as e:
            raise Exception(f"Error al cambiar contraseña: {str(e)}")
    
    def get_user_activity(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener actividad del usuario
        """
        try:
            return self.get_activity_use_case.execute(user_id)
        except Exception as e:
            raise Exception(f"Error al obtener actividad: {str(e)}")
    
    def validate_username(self, username: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validar disponibilidad de username
        """
        try:
            return self.validate_data_use_case.execute_username(username, user_id)
        except Exception as e:
            return {'valid': False, 'message': f"Error en validación: {str(e)}"}
    
    def validate_email(self, email: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validar email
        """
        try:
            return self.validate_data_use_case.execute_email(email, user_id)
        except Exception as e:
            return {'valid': False, 'message': f"Error en validación: {str(e)}"}
    
    def get_profile_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener resumen del perfil para dashboard
        """
        try:
            profile = self.get_profile_use_case.execute(user_id)
            activity = self.get_activity_use_case.execute(user_id)
            
            return {
                'basic_info': {
                    'username': profile['username'],
                    'full_name': profile['full_name'],
                    'email': profile['email'],
                    'role': profile['role']
                },
                'status': {
                    'is_active': profile['is_active'],
                    'profile_completion': profile['profile_completion'],
                    'last_login': activity['last_login'],
                    'account_age_days': activity['account_age_days']
                },
                'permissions': profile['permissions']
            }
        except Exception as e:
            raise Exception(f"Error al obtener resumen de perfil: {str(e)}")
