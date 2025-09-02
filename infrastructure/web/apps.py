"""
Configuración de la aplicación web de DESS
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class WebConfig(AppConfig):
    """
    Configuración de la aplicación web.
    Inicializa el contenedor de dependencias.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.web'
    verbose_name = 'DESS Web Infrastructure'
    
    def ready(self):
        """
        Se ejecuta cuando Django ha cargado completamente la aplicación.
        Ideal para inicializar el contenedor DI.
        """
        try:
            # Configurar el contenedor de dependencias
            from infrastructure.dependency_injection import setup_dependencies
            setup_dependencies()
            logger.info("Dependency injection container initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dependency container: {str(e)}")
            # No raise exception para no romper Django startup
        
        # Importar señales si existen
        try:
            from . import signals
        except ImportError:
            pass
