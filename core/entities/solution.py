"""
Entidad Solution - Modelo de dominio puro para soluciones empresariales
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
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


@dataclass
class Solution:
    """
    Entidad Solution - Representa una solución empresarial en el dominio
    
    Contiene la lógica de negocio pura sin dependencias externas.
    """
    # Identificación
    id: Optional[int]
    name: str
    description: str
    repository_url: str
    solution_type: SolutionType
    version: str
    
    # Estado
    status: SolutionStatus = SolutionStatus.INACTIVE
    is_public: bool = False
    
    # Metadatos
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    
    # Configuración
    environment_vars: Dict[str, str] = field(default_factory=dict)
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        self.validate()
        
        # Establecer timestamps si no están definidos
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def validate(self):
        """Validar todos los campos de la entidad"""
        self._validate_name()
        self._validate_description()
        self._validate_repository_url()
        self._validate_version()
        self._validate_solution_type()
    
    def _validate_name(self):
        """Validar nombre de la solución"""
        if not self.name or len(self.name.strip()) < ValidationConstants.MIN_SOLUTION_NAME_LENGTH:
            raise ValueError(f"El nombre debe tener al menos {ValidationConstants.MIN_SOLUTION_NAME_LENGTH} caracteres")
        
        if len(self.name) > ValidationConstants.MAX_SOLUTION_NAME_LENGTH:
            raise ValueError(f"El nombre no puede exceder {ValidationConstants.MAX_SOLUTION_NAME_LENGTH} caracteres")
        
        # Validar caracteres permitidos (alfanuméricos, espacios, guiones)
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', self.name):
            raise ValueError("El nombre solo puede contener letras, números, espacios, guiones y puntos")
    
    def _validate_description(self):
        """Validar descripción"""
        if not self.description or len(self.description.strip()) < ValidationConstants.MIN_SOLUTION_DESCRIPTION_LENGTH:
            raise ValueError(f"La descripción debe tener al menos {ValidationConstants.MIN_SOLUTION_DESCRIPTION_LENGTH} caracteres")
        
        if len(self.description) > ValidationConstants.MAX_SOLUTION_DESCRIPTION_LENGTH:
            raise ValueError(f"La descripción no puede exceder {ValidationConstants.MAX_SOLUTION_DESCRIPTION_LENGTH} caracteres")
    
    def _validate_repository_url(self):
        """Validar URL del repositorio"""
        if not self.repository_url:
            raise ValueError("La URL del repositorio es obligatoria")
        
        # Validar formato básico de URL
        url_pattern = r'^https?://.+\..+'
        if not re.match(url_pattern, self.repository_url):
            raise ValueError("La URL del repositorio debe ser válida (http/https)")
    
    def _validate_version(self):
        """Validar versión semántica"""
        if not self.version:
            raise ValueError("La versión es obligatoria")
        
        # Validar formato de versión semántica básica (x.y.z)
        version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?$'
        if not re.match(version_pattern, self.version):
            raise ValueError("La versión debe seguir el formato semántico (ej: 1.0.0)")
    
    def _validate_solution_type(self):
        """Validar tipo de solución"""
        if not isinstance(self.solution_type, SolutionType):
            raise ValueError("El tipo de solución debe ser un SolutionType válido")
    
    # Métodos de consulta (query methods)
    def is_active(self) -> bool:
        """Verificar si la solución está activa"""
        return self.status == SolutionStatus.ACTIVE
    
    def is_deployed(self) -> bool:
        """Verificar si la solución está desplegada"""
        return self.status == SolutionStatus.DEPLOYED
    
    def is_available_for_users(self) -> bool:
        """Verificar si la solución está disponible para usuarios"""
        return self.status in [SolutionStatus.ACTIVE, SolutionStatus.DEPLOYED]
    
    def is_in_maintenance(self) -> bool:
        """Verificar si está en mantenimiento"""
        return self.status == SolutionStatus.MAINTENANCE
    
    def has_failed(self) -> bool:
        """Verificar si el despliegue falló"""
        return self.status == SolutionStatus.FAILED
    
    # Métodos de comando (command methods)
    def activate(self):
        """Activar la solución"""
        if self.status == SolutionStatus.INACTIVE:
            self.status = SolutionStatus.ACTIVE
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"No se puede activar una solución en estado {self.status.value}")
    
    def deactivate(self):
        """Desactivar la solución"""
        if self.is_available_for_users():
            self.status = SolutionStatus.INACTIVE
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"No se puede desactivar una solución en estado {self.status.value}")
    
    def set_maintenance_mode(self):
        """Poner la solución en modo mantenimiento"""
        if self.is_available_for_users():
            self.status = SolutionStatus.MAINTENANCE
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"No se puede poner en mantenimiento una solución en estado {self.status.value}")
    
    def deploy(self, access_url: str = None, deployment_version: str = None):
        """Marcar la solución como desplegada"""
        if self.status in [SolutionStatus.ACTIVE, SolutionStatus.PENDING]:
            self.status = SolutionStatus.DEPLOYED
            self.deployed_at = datetime.now()
            self.updated_at = datetime.now()
            
            # Actualizar información de despliegue si se proporciona
            if access_url:
                self.deployment_config['access_url'] = access_url
            
            if deployment_version:
                self.deployment_config['deployed_version'] = deployment_version
        else:
            raise ValueError(f"No se puede desplegar una solución en estado {self.status.value}")
    
    def set_deployment_failed(self):
        """Marcar el despliegue como fallido"""
        self.status = SolutionStatus.FAILED
        self.updated_at = datetime.now()
    
    def archive(self):
        """Archivar la solución"""
        if self.status != SolutionStatus.DEPLOYED:
            self.status = SolutionStatus.ARCHIVED
            self.updated_at = datetime.now()
        else:
            raise ValueError("No se puede archivar una solución desplegada")
    
    # Métodos de configuración
    def add_environment_variable(self, key: str, value: str):
        """Agregar variable de entorno"""
        if not key or not isinstance(key, str):
            raise ValueError("La clave de la variable de entorno debe ser una cadena válida")
        
        self.environment_vars[key] = value
        self.updated_at = datetime.now()
    
    def remove_environment_variable(self, key: str):
        """Remover variable de entorno"""
        if key in self.environment_vars:
            del self.environment_vars[key]
            self.updated_at = datetime.now()
    
    def update_deployment_config(self, config: Dict[str, Any]):
        """Actualizar configuración de despliegue"""
        if not isinstance(config, dict):
            raise ValueError("La configuración debe ser un diccionario")
        
        self.deployment_config.update(config)
        self.updated_at = datetime.now()
    
    def update_metadata(self, metadata: Dict[str, Any]):
        """Actualizar metadatos"""
        if not isinstance(metadata, dict):
            raise ValueError("Los metadatos deben ser un diccionario")
        
        self.metadata.update(metadata)
        self.updated_at = datetime.now()
    
    # Métodos de salud y monitoreo
    def health_check_passed(self):
        """Marcar que el health check pasó"""
        self.last_health_check = datetime.now()
    
    def get_uptime(self) -> Optional[int]:
        """Obtener tiempo de actividad en segundos desde el despliegue"""
        if self.deployed_at and self.is_deployed():
            return int((datetime.now() - self.deployed_at).total_seconds())
        return None
    
    # Métodos de representación
    def __str__(self) -> str:
        return f"Solution(name='{self.name}', type='{self.solution_type.value}', status='{self.status.value}')"
    
    def __repr__(self) -> str:
        return (f"Solution(id={self.id}, name='{self.name}', "
                f"type={self.solution_type.value}, status={self.status.value})")
    
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
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'environment_vars': self.environment_vars,
            'deployment_config': self.deployment_config,
            'metadata': self.metadata
        }
