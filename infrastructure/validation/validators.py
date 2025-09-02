"""
Validadores robustos para entidades de DESS
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from infrastructure.exceptions.business_exceptions import ValidationError

logger = logging.getLogger(__name__)


class BaseValidator:
    """
    Validador base con funcionalidades comunes.
    """
    
    def __init__(self):
        self.errors: Dict[str, List[str]] = {}
    
    def add_error(self, field: str, message: str) -> None:
        """Agregar error de validación"""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)
    
    def is_valid(self) -> bool:
        """Verificar si la validación es exitosa"""
        return len(self.errors) == 0
    
    def get_errors(self) -> Dict[str, List[str]]:
        """Obtener todos los errores de validación"""
        return self.errors
    
    def clear_errors(self) -> None:
        """Limpiar todos los errores"""
        self.errors = {}
    
    def raise_if_invalid(self) -> None:
        """Lanzar ValidationError si hay errores"""
        if not self.is_valid():
            raise ValidationError("Errores de validación encontrados", self.errors)


class UserValidator(BaseValidator):
    """
    Validador especializado para usuarios.
    """
    
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]{3,30}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate_create_user(self, username: str, email: str, full_name: str, 
                           password: str, role: str) -> bool:
        """Validar datos para creación de usuario"""
        self.clear_errors()
        
        self._validate_username(username)
        self._validate_email(email)
        self._validate_full_name(full_name)
        self._validate_password(password)
        self._validate_role(role)
        
        return self.is_valid()
    
    def validate_update_user(self, username: str, email: str, full_name: str, 
                           role: Optional[str] = None) -> bool:
        """Validar datos para actualización de usuario"""
        self.clear_errors()
        
        self._validate_username(username)
        self._validate_email(email)
        self._validate_full_name(full_name)
        
        if role:
            self._validate_role(role)
        
        return self.is_valid()
    
    def _validate_username(self, username: str) -> None:
        """Validar nombre de usuario"""
        if not username:
            self.add_error('username', 'El nombre de usuario es requerido')
            return
        
        username = username.strip()
        
        if len(username) < 3:
            self.add_error('username', 'El nombre de usuario debe tener al menos 3 caracteres')
        
        if len(username) > 30:
            self.add_error('username', 'El nombre de usuario no puede tener más de 30 caracteres')
        
        if not self.USERNAME_PATTERN.match(username):
            self.add_error('username', 'El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos')
        
        # Palabras reservadas
        reserved_words = ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp']
        if username.lower() in reserved_words:
            self.add_error('username', 'Este nombre de usuario está reservado')
    
    def _validate_email(self, email: str) -> None:
        """Validar email"""
        if not email:
            self.add_error('email', 'El email es requerido')
            return
        
        email = email.strip().lower()
        
        if not self.EMAIL_PATTERN.match(email):
            self.add_error('email', 'Formato de email inválido')
        
        if len(email) > 254:
            self.add_error('email', 'El email es demasiado largo')
        
        # Dominios bloqueados (ejemplo)
        blocked_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1] if '@' in email else ''
        if domain in blocked_domains:
            self.add_error('email', 'Dominio de email no permitido')
    
    def _validate_full_name(self, full_name: str) -> None:
        """Validar nombre completo"""
        if not full_name:
            self.add_error('full_name', 'El nombre completo es requerido')
            return
        
        full_name = full_name.strip()
        
        if len(full_name) < 2:
            self.add_error('full_name', 'El nombre completo debe tener al menos 2 caracteres')
        
        if len(full_name) > 100:
            self.add_error('full_name', 'El nombre completo no puede tener más de 100 caracteres')
        
        # Verificar que no contenga números o caracteres especiales excesivos
        if re.search(r'\d{3,}', full_name):
            self.add_error('full_name', 'El nombre completo no puede contener secuencias largas de números')
        
        # Verificar que tenga al menos un espacio (nombre y apellido)
        if ' ' not in full_name.strip():
            self.add_error('full_name', 'Por favor incluye nombre y apellido')
    
    def _validate_password(self, password: str) -> None:
        """Validar contraseña con criterios de seguridad"""
        if not password:
            self.add_error('password', 'La contraseña es requerida')
            return
        
        if len(password) < 8:
            self.add_error('password', 'La contraseña debe tener al menos 8 caracteres')
        
        if len(password) > 128:
            self.add_error('password', 'La contraseña no puede tener más de 128 caracteres')
        
        # Criterios de complejidad
        criteria = {
            'uppercase': re.search(r'[A-Z]', password),
            'lowercase': re.search(r'[a-z]', password),
            'digit': re.search(r'\d', password),
            'special': re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        }
        
        missing_criteria = [k for k, v in criteria.items() if not v]
        
        if len(missing_criteria) > 1:
            self.add_error('password', 
                          f'La contraseña debe contener: mayúsculas, minúsculas, números y caracteres especiales')
        
        # Contraseñas comunes (ejemplo básico)
        common_passwords = ['password', '12345678', 'qwerty123', 'admin123']
        if password.lower() in common_passwords:
            self.add_error('password', 'Esta contraseña es demasiado común')
    
    def _validate_role(self, role: str) -> None:
        """Validar rol de usuario"""
        valid_roles = ['user', 'super_admin']
        
        if not role:
            self.add_error('role', 'El rol es requerido')
            return
        
        if role not in valid_roles:
            self.add_error('role', f'Rol inválido. Roles válidos: {", ".join(valid_roles)}')


class SolutionValidator(BaseValidator):
    """
    Validador especializado para soluciones.
    """
    
    def validate_create_solution(self, name: str, description: str, repository_url: str,
                               solution_type: str, version: str, access_url: Optional[str] = None) -> bool:
        """Validar datos para creación de solución"""
        self.clear_errors()
        
        self._validate_name(name)
        self._validate_description(description)
        self._validate_repository_url(repository_url)
        self._validate_solution_type(solution_type)
        self._validate_version(version)
        
        if access_url:
            self._validate_access_url(access_url)
        
        return self.is_valid()
    
    def _validate_name(self, name: str) -> None:
        """Validar nombre de solución"""
        if not name:
            self.add_error('name', 'El nombre es requerido')
            return
        
        name = name.strip()
        
        if len(name) < 3:
            self.add_error('name', 'El nombre debe tener al menos 3 caracteres')
        
        if len(name) > 100:
            self.add_error('name', 'El nombre no puede tener más de 100 caracteres')
        
        # Verificar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', name):
            self.add_error('name', 'El nombre solo puede contener letras, números, espacios y guiones')
    
    def _validate_description(self, description: str) -> None:
        """Validar descripción"""
        if not description:
            self.add_error('description', 'La descripción es requerida')
            return
        
        description = description.strip()
        
        if len(description) < 10:
            self.add_error('description', 'La descripción debe tener al menos 10 caracteres')
        
        if len(description) > 1000:
            self.add_error('description', 'La descripción no puede tener más de 1000 caracteres')
    
    def _validate_repository_url(self, repository_url: str) -> None:
        """Validar URL del repositorio"""
        if not repository_url:
            self.add_error('repository_url', 'La URL del repositorio es requerida')
            return
        
        try:
            parsed = urlparse(repository_url)
            
            if not parsed.scheme or not parsed.netloc:
                self.add_error('repository_url', 'URL de repositorio inválida')
                return
            
            if parsed.scheme not in ['http', 'https']:
                self.add_error('repository_url', 'La URL debe usar HTTP o HTTPS')
            
            # Validar dominios de repositorios conocidos
            valid_domains = ['github.com', 'gitlab.com', 'bitbucket.org']
            if not any(domain in parsed.netloc for domain in valid_domains):
                logger.warning(f"Repository URL uses unknown domain: {parsed.netloc}")
            
        except Exception:
            self.add_error('repository_url', 'Formato de URL inválido')
    
    def _validate_solution_type(self, solution_type: str) -> None:
        """Validar tipo de solución"""
        valid_types = [
            'web_app', 'mobile_app', 'desktop_app', 'api_service',
            'microservice', 'database', 'integration', 'analytics', 'other'
        ]
        
        if not solution_type:
            self.add_error('solution_type', 'El tipo de solución es requerido')
            return
        
        if solution_type not in valid_types:
            self.add_error('solution_type', f'Tipo inválido. Tipos válidos: {", ".join(valid_types)}')
    
    def _validate_version(self, version: str) -> None:
        """Validar versión semántica"""
        if not version:
            self.add_error('version', 'La versión es requerida')
            return
        
        # Patrón semver básico: x.y.z con posibles sufijos
        semver_pattern = r'^\d+\.\d+\.\d+(-[\w\.-]+)?(\+[\w\.-]+)?$'
        
        if not re.match(semver_pattern, version):
            self.add_error('version', 'La versión debe seguir el formato semántico (x.y.z)')
    
    def _validate_access_url(self, access_url: str) -> None:
        """Validar URL de acceso"""
        try:
            parsed = urlparse(access_url)
            
            if not parsed.scheme or not parsed.netloc:
                self.add_error('access_url', 'URL de acceso inválida')
                return
            
            if parsed.scheme not in ['http', 'https']:
                self.add_error('access_url', 'La URL de acceso debe usar HTTP o HTTPS')
                
        except Exception:
            self.add_error('access_url', 'Formato de URL de acceso inválido')


class AssignmentValidator(BaseValidator):
    """
    Validador para asignaciones de soluciones.
    """
    
    def validate_assignment(self, user_id: int, solution_id: int) -> bool:
        """Validar asignación de solución a usuario"""
        self.clear_errors()
        
        if not isinstance(user_id, int) or user_id <= 0:
            self.add_error('user_id', 'ID de usuario inválido')
        
        if not isinstance(solution_id, int) or solution_id <= 0:
            self.add_error('solution_id', 'ID de solución inválido')
        
        return self.is_valid()
    
    def validate_bulk_assignment(self, user_ids: List[int], solution_ids: List[int]) -> bool:
        """Validar asignación masiva"""
        self.clear_errors()
        
        if not user_ids:
            self.add_error('user_ids', 'Debe seleccionar al menos un usuario')
        
        if not solution_ids:
            self.add_error('solution_ids', 'Debe seleccionar al menos una solución')
        
        if len(user_ids) > 100:
            self.add_error('user_ids', 'No se pueden asignar más de 100 usuarios a la vez')
        
        if len(solution_ids) > 50:
            self.add_error('solution_ids', 'No se pueden asignar más de 50 soluciones a la vez')
        
        return self.is_valid()


class InputSanitizer:
    """
    Sanitizador de entrada para prevenir ataques.
    """
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitizar string básico"""
        if not isinstance(value, str):
            return str(value)
        
        # Eliminar caracteres de control
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Trimear espacios
        sanitized = sanitized.strip()
        
        # Limitar longitud
        if max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_html_input(value: str) -> str:
        """Sanitizar entrada que podría contener HTML"""
        if not isinstance(value, str):
            return str(value)
        
        # Caracteres peligrosos básicos
        dangerous_chars = {'<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;', '&': '&amp;'}
        
        sanitized = value
        for char, replacement in dangerous_chars.items():
            sanitized = sanitized.replace(char, replacement)
        
        return sanitized
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Sanitizar entrada para prevenir SQL injection básica"""
        if not isinstance(value, str):
            return str(value)
        
        # Patrones peligrosos básicos
        dangerous_patterns = [
            r"';\s*(drop|delete|truncate|update)\s+",
            r"union\s+select",
            r";\s*--",
            r"'.*or.*'.*'",
        ]
        
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized