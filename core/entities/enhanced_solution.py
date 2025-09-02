"""
Entidad Solution mejorada con más lógica de negocio
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
import re
from core.constants import ValidationConstants


class SolutionStatus(Enum):
    """Estados posibles de una solución"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPLOYED = "deployed"
    MAINTENANCE = "maintenance"
    PENDING = "pending"
    FAILED = "failed"
    ARCHIVED = "archived"


class SolutionType(Enum):
    """Tipos de solución empresarial"""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    DATABASE = "database"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    OTHER = "other"


class SolutionPriority(Enum):
    """Prioridad de la solución"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SolutionMetrics:
    """Métricas de rendimiento de la solución"""
    uptime_percentage: float = 0.0
    response_time_ms: int = 0
    daily_users: int = 0
    error_rate: float = 0.0
    last_updated: Optional[datetime] = None


@dataclass
class EnhancedSolution:
    """
    Entidad Solution mejorada con lógica de negocio rica.
    Representa una solución empresarial con funcionalidades avanzadas.
    """
    # Identificación básica
    id: Optional[int]
    name: str
    description: str
    repository_url: str
    solution_type: SolutionType
    version: str
    
    # Estado y configuración
    status: SolutionStatus = SolutionStatus.PENDING
    priority: SolutionPriority = SolutionPriority.MEDIUM
    access_url: Optional[str] = None
    
    # Metadatos temporales
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    
    # Configuración avanzada
    tags: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    # Métricas y monitoreo
    metrics: SolutionMetrics = field(default_factory=SolutionMetrics)
    
    # Configuración de mantenimiento
    maintenance_window_start: Optional[datetime] = None
    maintenance_window_end: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        self.validate()
    
    def validate(self) -> None:
        """Validar la entidad según reglas de negocio"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 3:
            errors.append("El nombre debe tener al menos 3 caracteres")
        
        if not self.description or len(self.description.strip()) < 10:
            errors.append("La descripción debe tener al menos 10 caracteres")
        
        if not self._is_valid_repository_url():
            errors.append("URL del repositorio no válida")
        
        if not self._is_valid_version():
            errors.append("Formato de versión no válido (debe ser semver: x.y.z)")
        
        if self.access_url and not self._is_valid_access_url():
            errors.append("URL de acceso no válida")
        
        if errors:
            raise ValueError("; ".join(errors))
    
    def _is_valid_repository_url(self) -> bool:
        """Validar URL del repositorio"""
        if not self.repository_url:
            return False
        
        # Patrones comunes para repositorios
        patterns = [
            r'https://github\.com/.+/.+',
            r'https://gitlab\.com/.+/.+',
            r'https://bitbucket\.org/.+/.+',
            r'https://.+\.git',
        ]
        
        return any(re.match(pattern, self.repository_url) for pattern in patterns)
    
    def _is_valid_version(self) -> bool:
        """Validar formato de versión (semver)"""
        if not self.version:
            return False
        
        # Patrón semver básico: x.y.z
        pattern = r'^\d+\.\d+\.\d+(-[\w\.-]+)?(\+[\w\.-]+)?$'
        return bool(re.match(pattern, self.version))
    
    def _is_valid_access_url(self) -> bool:
        """Validar URL de acceso"""
        if not self.access_url:
            return True  # Es opcional
        
        pattern = r'https?://.+'
        return bool(re.match(pattern, self.access_url))
    
    def is_accessible(self) -> bool:
        """Verificar si la solución es accesible por usuarios"""
        return (
            self.status == SolutionStatus.ACTIVE and
            self.access_url is not None and
            not self.is_in_maintenance_window()
        )
    
    def is_in_maintenance_window(self) -> bool:
        """Verificar si está en ventana de mantenimiento"""
        if not self.maintenance_window_start or not self.maintenance_window_end:
            return False
        
        now = datetime.now()
        return self.maintenance_window_start <= now <= self.maintenance_window_end
    
    def get_health_score(self) -> int:
        """Calcular puntaje de salud (0-100)"""
        score = 100
        
        # Reducir por tiempo de inactividad
        if self.metrics.uptime_percentage < 99:
            score -= int((99 - self.metrics.uptime_percentage) * 2)
        
        # Reducir por tiempo de respuesta alto
        if self.metrics.response_time_ms > 1000:
            score -= min(20, int((self.metrics.response_time_ms - 1000) / 100))
        
        # Reducir por tasa de errores alta
        if self.metrics.error_rate > 1:
            score -= int(self.metrics.error_rate * 10)
        
        # Reducir si no está activa
        if self.status != SolutionStatus.ACTIVE:
            score -= 30
        
        # Reducir si no tiene URL de acceso
        if not self.access_url:
            score -= 20
        
        return max(0, score)
    
    def can_be_deleted(self) -> tuple[bool, Optional[str]]:
        """Verificar si la solución puede ser eliminada"""
        if self.status == SolutionStatus.ACTIVE and self.metrics.daily_users > 0:
            return False, "No se puede eliminar una solución activa con usuarios"
        
        if self.status == SolutionStatus.DEPLOYED:
            return False, "No se puede eliminar una solución desplegada"
        
        return True, None
    
    def increment_version(self, version_type: str = "patch") -> str:
        """Incrementar versión automáticamente"""
        if not self._is_valid_version():
            return "1.0.0"
        
        parts = self.version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        return new_version
    
    def add_tag(self, tag: str) -> None:
        """Agregar tag si no existe"""
        if tag and tag not in self.tags:
            self.tags.append(tag.strip().lower())
    
    def remove_tag(self, tag: str) -> bool:
        """Remover tag si existe"""
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def set_environment_variable(self, key: str, value: str) -> None:
        """Establecer variable de entorno"""
        if key and value:
            self.environment_variables[key] = value
    
    def get_environment_variable(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Obtener variable de entorno"""
        return self.environment_variables.get(key, default)
    
    def add_dependency(self, dependency: str) -> None:
        """Agregar dependencia"""
        if dependency and dependency not in self.dependencies:
            self.dependencies.append(dependency)
    
    def remove_dependency(self, dependency: str) -> bool:
        """Remover dependencia"""
        if dependency in self.dependencies:
            self.dependencies.remove(dependency)
            return True
        return False
    
    def update_metrics(self, 
                      uptime_percentage: Optional[float] = None,
                      response_time_ms: Optional[int] = None,
                      daily_users: Optional[int] = None,
                      error_rate: Optional[float] = None) -> None:
        """Actualizar métricas de rendimiento"""
        if uptime_percentage is not None:
            self.metrics.uptime_percentage = max(0.0, min(100.0, uptime_percentage))
        
        if response_time_ms is not None:
            self.metrics.response_time_ms = max(0, response_time_ms)
        
        if daily_users is not None:
            self.metrics.daily_users = max(0, daily_users)
        
        if error_rate is not None:
            self.metrics.error_rate = max(0.0, error_rate)
        
        self.metrics.last_updated = datetime.now()
    
    def schedule_maintenance(self, start_time: datetime, end_time: datetime) -> None:
        """Programar ventana de mantenimiento"""
        if start_time >= end_time:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")
        
        if start_time <= datetime.now():
            raise ValueError("La ventana de mantenimiento debe ser en el futuro")
        
        self.maintenance_window_start = start_time
        self.maintenance_window_end = end_time
    
    def clear_maintenance_window(self) -> None:
        """Limpiar ventana de mantenimiento"""
        self.maintenance_window_start = None
        self.maintenance_window_end = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'repository_url': self.repository_url,
            'solution_type': self.solution_type.value,
            'version': self.version,
            'status': self.status.value,
            'priority': self.priority.value,
            'access_url': self.access_url,
            'tags': self.tags,
            'health_score': self.get_health_score(),
            'is_accessible': self.is_accessible(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }