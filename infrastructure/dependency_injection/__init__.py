"""
Sistema de Inyección de Dependencias de DESS
"""
from .container import DIContainer, container, get_container, reset_container, inject
from .setup import setup_dependencies

__all__ = [
    'DIContainer',
    'container', 
    'get_container',
    'reset_container',
    'inject',
    'setup_dependencies',
]