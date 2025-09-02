"""
Contenedor de Inyección de Dependencias para DESS
Implementación del patrón Dependency Injection Container
"""
from typing import Dict, Callable, Any, Type, TypeVar
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """
    Contenedor de Inyección de Dependencias simple pero poderoso.
    Maneja el ciclo de vida de las dependencias y su resolución.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """
        Registrar un servicio como singleton (una instancia para toda la app).
        """
        service_name = self._get_service_name(interface)
        
        def factory():
            if service_name not in self._singletons:
                # Resolver dependencias del constructor
                dependencies = self._resolve_constructor_dependencies(implementation)
                self._singletons[service_name] = implementation(**dependencies)
            return self._singletons[service_name]
        
        self._factories[service_name] = factory
        logger.debug(f"Registered singleton: {service_name}")
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """
        Registrar un servicio como transient (nueva instancia en cada resolución).
        """
        service_name = self._get_service_name(interface)
        
        def factory():
            # Resolver dependencias del constructor
            dependencies = self._resolve_constructor_dependencies(implementation)
            return implementation(**dependencies)
        
        self._factories[service_name] = factory
        logger.debug(f"Registered transient: {service_name}")
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """
        Registrar una instancia específica.
        """
        service_name = self._get_service_name(interface)
        self._singletons[service_name] = instance
        self._factories[service_name] = lambda: instance
        logger.debug(f"Registered instance: {service_name}")
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """
        Registrar una factory personalizada.
        """
        service_name = self._get_service_name(interface)
        self._factories[service_name] = factory
        logger.debug(f"Registered factory: {service_name}")
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolver una dependencia.
        """
        service_name = self._get_service_name(interface)
        
        if service_name not in self._factories:
            raise ValueError(f"Service {service_name} not registered")
        
        try:
            return self._factories[service_name]()
        except Exception as e:
            logger.error(f"Error resolving {service_name}: {str(e)}")
            raise
    
    def _get_service_name(self, interface: Type) -> str:
        """
        Obtener nombre del servicio desde el tipo.
        """
        return f"{interface.__module__}.{interface.__name__}"
    
    def _resolve_constructor_dependencies(self, implementation: Type) -> Dict[str, Any]:
        """
        Resolver automáticamente las dependencias del constructor.
        """
        import inspect
        
        dependencies = {}
        sig = inspect.signature(implementation.__init__)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param.annotation == inspect.Parameter.empty:
                logger.warning(f"Parameter {param_name} in {implementation.__name__} has no type annotation")
                continue
            
            # Intentar resolver la dependencia
            try:
                dependency = self.resolve(param.annotation)
                dependencies[param_name] = dependency
            except ValueError:
                if param.default == inspect.Parameter.empty:
                    logger.error(f"Cannot resolve required dependency {param_name} for {implementation.__name__}")
                    raise ValueError(f"Cannot resolve dependency: {param.annotation}")
                else:
                    # Usar valor por defecto si está disponible
                    dependencies[param_name] = param.default
        
        return dependencies


# Instancia global del contenedor
container = DIContainer()


def get_container() -> DIContainer:
    """
    Obtener la instancia global del contenedor.
    """
    return container


def reset_container() -> None:
    """
    Resetear el contenedor (útil para testing).
    """
    global container
    container = DIContainer()


# Decorador para inyección automática
def inject(func: Callable) -> Callable:
    """
    Decorador para inyección automática de dependencias en funciones/métodos.
    """
    import inspect
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        
        # Resolver dependencias faltantes
        for param_name, param in sig.parameters.items():
            if param_name not in bound.arguments:
                if param.annotation != inspect.Parameter.empty:
                    try:
                        dependency = container.resolve(param.annotation)
                        bound.arguments[param_name] = dependency
                    except ValueError:
                        if param.default == inspect.Parameter.empty:
                            raise ValueError(f"Cannot resolve dependency: {param.annotation}")
        
        return func(**bound.arguments)
    
    return wrapper