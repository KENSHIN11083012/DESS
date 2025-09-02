"""
Reglas de validación centralizadas para DESS
"""
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from infrastructure.database.models import DESSUser, Solution


class ValidationRules:
    """
    Reglas de validación centralizadas y reutilizables.
    """
    
    # Expresiones regulares comunes
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]{3,30}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+(-[\w\.-]+)?(\+[\w\.-]+)?$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$')
    
    # Listas de valores válidos
    VALID_USER_ROLES = ['user', 'super_admin']
    VALID_SOLUTION_TYPES = [
        'web_app', 'mobile_app', 'desktop_app', 'api_service',
        'microservice', 'database', 'integration', 'analytics', 'other'
    ]
    
    # Palabras reservadas y bloqueadas
    RESERVED_USERNAMES = ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp', 'dess']
    BLOCKED_EMAIL_DOMAINS = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
    COMMON_PASSWORDS = ['password', '12345678', 'qwerty123', 'admin123', 'password123']
    
    @classmethod
    def validate_username_format(cls, username: str) -> Tuple[bool, Optional[str]]:
        """Validar formato de nombre de usuario"""
        if not username:
            return False, "El nombre de usuario es requerido"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres"
        
        if len(username) > 30:
            return False, "El nombre de usuario no puede tener más de 30 caracteres"
        
        if not cls.USERNAME_PATTERN.match(username):
            return False, "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos"
        
        if username.lower() in cls.RESERVED_USERNAMES:
            return False, "Este nombre de usuario está reservado"
        
        return True, None
    
    @classmethod
    def validate_username_uniqueness(cls, username: str, exclude_user_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validar unicidad de nombre de usuario"""
        try:
            query = User.objects.filter(username=username)
            if exclude_user_id:
                query = query.exclude(id=exclude_user_id)
            
            if query.exists():
                return False, "Este nombre de usuario ya está en uso"
            
            return True, None
        except Exception:
            return False, "Error verificando la disponibilidad del nombre de usuario"
    
    @classmethod
    def validate_email_format(cls, email: str) -> Tuple[bool, Optional[str]]:
        """Validar formato de email"""
        if not email:
            return False, "El email es requerido"
        
        email = email.strip().lower()
        
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Formato de email inválido"
        
        if len(email) > 254:
            return False, "El email es demasiado largo"
        
        # Verificar dominios bloqueados
        domain = email.split('@')[1] if '@' in email else ''
        if domain in cls.BLOCKED_EMAIL_DOMAINS:
            return False, "Dominio de email no permitido"
        
        return True, None
    
    @classmethod
    def validate_email_uniqueness(cls, email: str, exclude_user_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validar unicidad de email"""
        try:
            query = User.objects.filter(email=email.lower())
            if exclude_user_id:
                query = query.exclude(id=exclude_user_id)
            
            if query.exists():
                return False, "Este email ya está registrado"
            
            return True, None
        except Exception:
            return False, "Error verificando la disponibilidad del email"
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """Validar fortaleza de contraseña"""
        errors = []
        
        if not password:
            return False, ["La contraseña es requerida"]
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if len(password) > 128:
            errors.append("La contraseña no puede tener más de 128 caracteres")
        
        # Criterios de complejidad
        criteria = {
            'uppercase': (re.search(r'[A-Z]', password), "al menos una letra mayúscula"),
            'lowercase': (re.search(r'[a-z]', password), "al menos una letra minúscula"),
            'digit': (re.search(r'\d', password), "al menos un número"),
            'special': (re.search(r'[!@#$%^&*(),.?":{}|<>]', password), "al menos un carácter especial")
        }
        
        missing_criteria = []
        for criterion, (found, description) in criteria.items():
            if not found:
                missing_criteria.append(description)
        
        if len(missing_criteria) > 1:
            errors.append(f"La contraseña debe contener: {', '.join(missing_criteria)}")
        
        # Verificar contraseñas comunes
        if password.lower() in cls.COMMON_PASSWORDS:
            errors.append("Esta contraseña es demasiado común")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_solution_name_uniqueness(cls, name: str, exclude_solution_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validar unicidad del nombre de solución"""
        try:
            query = Solution.objects.filter(name__iexact=name.strip())
            if exclude_solution_id:
                query = query.exclude(id=exclude_solution_id)
            
            if query.exists():
                return False, "Ya existe una solución con este nombre"
            
            return True, None
        except Exception:
            return False, "Error verificando la disponibilidad del nombre"
    
    @classmethod
    def validate_repository_url_uniqueness(cls, repository_url: str, exclude_solution_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validar unicidad de URL de repositorio"""
        try:
            query = Solution.objects.filter(repository_url=repository_url)
            if exclude_solution_id:
                query = query.exclude(id=exclude_solution_id)
            
            if query.exists():
                return False, "Esta URL de repositorio ya está registrada"
            
            return True, None
        except Exception:
            return False, "Error verificando la disponibilidad de la URL"
    
    @classmethod
    def validate_user_assignment_limits(cls, user_id: int) -> Tuple[bool, Optional[str]]:
        """Validar límites de asignación de soluciones por usuario"""
        try:
            user = DESSUser.objects.get(id=user_id)
            current_assignments = user.assigned_solutions.count()
            
            # Límite basado en rol
            max_assignments = {
                'user': 10,
                'super_admin': 50
            }.get(user.role, 5)
            
            if current_assignments >= max_assignments:
                return False, f"El usuario ha alcanzado el límite máximo de {max_assignments} soluciones asignadas"
            
            return True, None
        except DESSUser.DoesNotExist:
            return False, "Usuario no encontrado"
        except Exception:
            return False, "Error verificando límites de asignación"
    
    @classmethod
    def validate_solution_assignment_limits(cls, solution_id: int) -> Tuple[bool, Optional[str]]:
        """Validar límites de usuarios asignados por solución"""
        try:
            solution = Solution.objects.get(id=solution_id)
            current_users = solution.assigned_users.count()
            
            # Límite máximo de usuarios por solución
            max_users = 100
            
            if current_users >= max_users:
                return False, f"La solución ha alcanzado el límite máximo de {max_users} usuarios asignados"
            
            return True, None
        except Solution.DoesNotExist:
            return False, "Solución no encontrada"
        except Exception:
            return False, "Error verificando límites de asignación"
    
    @classmethod
    def validate_bulk_assignment_limits(cls, user_ids: List[int], solution_ids: List[int]) -> Tuple[bool, List[str]]:
        """Validar límites para asignaciones masivas"""
        errors = []
        
        if len(user_ids) > 100:
            errors.append("No se pueden asignar más de 100 usuarios a la vez")
        
        if len(solution_ids) > 50:
            errors.append("No se pueden asignar más de 50 soluciones a la vez")
        
        # Verificar que los usuarios existen
        existing_users = set(DESSUser.objects.filter(id__in=user_ids).values_list('id', flat=True))
        missing_users = set(user_ids) - existing_users
        if missing_users:
            errors.append(f"Usuarios no encontrados: {', '.join(map(str, missing_users))}")
        
        # Verificar que las soluciones existen
        existing_solutions = set(Solution.objects.filter(id__in=solution_ids).values_list('id', flat=True))
        missing_solutions = set(solution_ids) - existing_solutions
        if missing_solutions:
            errors.append(f"Soluciones no encontradas: {', '.join(map(str, missing_solutions))}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_date_range(cls, start_date: Optional[datetime], end_date: Optional[datetime]) -> Tuple[bool, Optional[str]]:
        """Validar rango de fechas"""
        if not start_date or not end_date:
            return True, None
        
        if start_date >= end_date:
            return False, "La fecha de inicio debe ser anterior a la fecha de fin"
        
        # No permitir rangos muy grandes (más de 2 años)
        if (end_date - start_date) > timedelta(days=730):
            return False, "El rango de fechas no puede ser mayor a 2 años"
        
        return True, None
    
    @classmethod
    def validate_pagination_params(cls, page: int, per_page: int) -> Tuple[bool, List[str]]:
        """Validar parámetros de paginación"""
        errors = []
        
        if page < 1:
            errors.append("El número de página debe ser mayor a 0")
        
        if per_page < 1:
            errors.append("El número de elementos por página debe ser mayor a 0")
        
        if per_page > 100:
            errors.append("No se pueden mostrar más de 100 elementos por página")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_search_query(cls, query: str) -> Tuple[bool, Optional[str]]:
        """Validar consulta de búsqueda"""
        if not query:
            return False, "La consulta de búsqueda no puede estar vacía"
        
        query = query.strip()
        
        if len(query) < 2:
            return False, "La consulta debe tener al menos 2 caracteres"
        
        if len(query) > 100:
            return False, "La consulta no puede tener más de 100 caracteres"
        
        # Verificar caracteres peligrosos
        dangerous_chars = ['<', '>', ';', '&', '|', '`']
        if any(char in query for char in dangerous_chars):
            return False, "La consulta contiene caracteres no permitidos"
        
        return True, None