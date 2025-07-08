"""
Validadores personalizados para las APIs de DESS
"""
from typing import Dict, Any, List, Optional
from core.constants import ValidationConstants
import re


class APIValidator:
    """
    Validador base para APIs.
    """
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validar que todos los campos requeridos estén presentes.
        
        Args:
            data: Datos a validar
            required_fields: Lista de campos requeridos
        
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                errors.append(f"El campo '{field}' es requerido")
        return errors
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: int, max_length: int) -> Optional[str]:
        """
        Validar longitud de string.
        
        Args:
            value: Valor a validar
            field_name: Nombre del campo
            min_length: Longitud mínima
            max_length: Longitud máxima
        
        Returns:
            Optional[str]: Mensaje de error si hay problema, None si es válido
        """
        if not isinstance(value, str):
            return f"El campo '{field_name}' debe ser una cadena de texto"
        
        if len(value) < min_length:
            return f"El campo '{field_name}' debe tener al menos {min_length} caracteres"
        
        if len(value) > max_length:
            return f"El campo '{field_name}' no puede tener más de {max_length} caracteres"
        
        return None
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """
        Validar formato de email.
        
        Args:
            email: Email a validar
        
        Returns:
            Optional[str]: Mensaje de error si hay problema, None si es válido
        """
        if not isinstance(email, str):
            return "El email debe ser una cadena de texto"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return "El formato del email no es válido"
        
        return None
    
    @staticmethod
    def validate_url(url: str, field_name: str = 'URL') -> Optional[str]:
        """
        Validar formato de URL.
        
        Args:
            url: URL a validar
            field_name: Nombre del campo
        
        Returns:
            Optional[str]: Mensaje de error si hay problema, None si es válido
        """
        if not isinstance(url, str):
            return f"El campo '{field_name}' debe ser una cadena de texto"
        
        url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        if not re.match(url_pattern, url):
            return f"El formato de la {field_name} no es válido"
        
        return None


class UserValidator(APIValidator):
    """
    Validador específico para datos de usuario.
    """
    
    @classmethod
    def validate_create_user_data(cls, data: Dict[str, Any]) -> List[str]:
        """
        Validar datos para crear usuario.
        
        Args:
            data: Datos del usuario
        
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        # Campos requeridos
        required_fields = ['username', 'email', 'password', 'full_name', 'role']
        errors.extend(cls.validate_required_fields(data, required_fields))
        
        # Validar username
        if 'username' in data:
            error = cls.validate_string_length(
                data['username'], 
                'username', 
                ValidationConstants.MIN_USERNAME_LENGTH, 
                ValidationConstants.MAX_USERNAME_LENGTH
            )
            if error:
                errors.append(error)
        
        # Validar email
        if 'email' in data:
            error = cls.validate_email(data['email'])
            if error:
                errors.append(error)
        
        # Validar password
        if 'password' in data:
            error = cls.validate_string_length(
                data['password'], 
                'password', 
                ValidationConstants.MIN_PASSWORD_LENGTH, 
                ValidationConstants.MAX_PASSWORD_LENGTH
            )
            if error:
                errors.append(error)
        
        # Validar full_name
        if 'full_name' in data:
            error = cls.validate_string_length(
                data['full_name'], 
                'full_name', 
                ValidationConstants.MIN_FULL_NAME_LENGTH, 
                ValidationConstants.MAX_FULL_NAME_LENGTH
            )
            if error:
                errors.append(error)
        
        # Validar role
        if 'role' in data:
            valid_roles = ['super_admin', 'user']
            if data['role'] not in valid_roles:
                errors.append(f"El rol debe ser uno de: {', '.join(valid_roles)}")
        
        return errors
    
    @classmethod
    def validate_update_user_data(cls, data: Dict[str, Any]) -> List[str]:
        """
        Validar datos para actualizar usuario.
        
        Args:
            data: Datos del usuario
        
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        # Solo validar campos presentes
        if 'username' in data:
            error = cls.validate_string_length(
                data['username'], 
                'username', 
                ValidationConstants.MIN_USERNAME_LENGTH, 
                ValidationConstants.MAX_USERNAME_LENGTH
            )
            if error:
                errors.append(error)
        
        if 'email' in data:
            error = cls.validate_email(data['email'])
            if error:
                errors.append(error)
        
        if 'full_name' in data:
            error = cls.validate_string_length(
                data['full_name'], 
                'full_name', 
                ValidationConstants.MIN_FULL_NAME_LENGTH, 
                ValidationConstants.MAX_FULL_NAME_LENGTH
            )
            if error:
                errors.append(error)
        
        if 'role' in data:
            valid_roles = ['super_admin', 'user']
            if data['role'] not in valid_roles:
                errors.append(f"El rol debe ser uno de: {', '.join(valid_roles)}")
        
        return errors


class SolutionValidator(APIValidator):
    """
    Validador específico para datos de solución.
    """
    
    @classmethod
    def validate_create_solution_data(cls, data: Dict[str, Any]) -> List[str]:
        """
        Validar datos para crear solución.
        
        Args:
            data: Datos de la solución
        
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        # Campos requeridos
        required_fields = ['name', 'description', 'repository_url', 'solution_type']
        errors.extend(cls.validate_required_fields(data, required_fields))
        
        # Validar name
        if 'name' in data:
            error = cls.validate_string_length(
                data['name'], 
                'name', 
                ValidationConstants.MIN_SOLUTION_NAME_LENGTH, 
                ValidationConstants.MAX_SOLUTION_NAME_LENGTH
            )
            if error:
                errors.append(error)
        
        # Validar description
        if 'description' in data:
            error = cls.validate_string_length(
                data['description'], 
                'description', 
                ValidationConstants.MIN_SOLUTION_DESCRIPTION_LENGTH, 
                ValidationConstants.MAX_SOLUTION_DESCRIPTION_LENGTH
            )
            if error:
                errors.append(error)
        
        # Validar repository_url
        if 'repository_url' in data:
            error = cls.validate_url(data['repository_url'], 'URL del repositorio')
            if error:
                errors.append(error)
        
        # Validar solution_type
        if 'solution_type' in data:
            valid_types = ['web', 'api', 'desktop', 'mobile', 'script']
            if data['solution_type'] not in valid_types:
                errors.append(f"El tipo de solución debe ser uno de: {', '.join(valid_types)}")
        
        return errors
    
    @classmethod
    def validate_update_solution_data(cls, data: Dict[str, Any]) -> List[str]:
        """
        Validar datos para actualizar solución.
        
        Args:
            data: Datos de la solución
        
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        # Solo validar campos presentes
        if 'name' in data:
            error = cls.validate_string_length(
                data['name'], 
                'name', 
                ValidationConstants.MIN_SOLUTION_NAME_LENGTH, 
                ValidationConstants.MAX_SOLUTION_NAME_LENGTH
            )
            if error:
                errors.append(error)
        
        if 'description' in data:
            error = cls.validate_string_length(
                data['description'], 
                'description', 
                ValidationConstants.MIN_SOLUTION_DESCRIPTION_LENGTH, 
                ValidationConstants.MAX_SOLUTION_DESCRIPTION_LENGTH
            )
            if error:
                errors.append(error)
        
        if 'repository_url' in data:
            error = cls.validate_url(data['repository_url'], 'URL del repositorio')
            if error:
                errors.append(error)
        
        if 'solution_type' in data:
            valid_types = ['web', 'api', 'desktop', 'mobile', 'script']
            if data['solution_type'] not in valid_types:
                errors.append(f"El tipo de solución debe ser uno de: {', '.join(valid_types)}")
        
        return errors
