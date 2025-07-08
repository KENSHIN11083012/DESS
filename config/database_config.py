# ============================================================================
# DATABASE CONFIGURATION FOR DESS - UNIFIED AND OPTIMIZED
# ============================================================================

import os
from pathlib import Path
from decouple import config

# Obtener BASE_DIR del archivo principal
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# CONFIGURACIÓN UNIFICADA DE BASE DE DATOS
# ============================================================================

class DatabaseConfigManager:
    """
    Manager unificado para configuración de base de datos
    Elimina redundancias y centraliza la lógica
    """
    
    def __init__(self):
        self.engine = config('DATABASE_ENGINE', default='sqlite')
        self.base_dir = BASE_DIR
    
    def get_database_config(self):
        """Retorna la configuración de BD según el engine seleccionado"""
        if self.engine.lower() == 'oracle':
            return self._get_oracle_config()
        else:
            return self._get_sqlite_config()
    
    def _get_oracle_config(self):
        """Configuración para Oracle Database"""
        return {
            'default': {
                'ENGINE': 'django.db.backends.oracle',
                'NAME': config('ORACLE_SERVICE_NAME', default='XEPDB1'),
                'USER': config('ORACLE_USER', default='dess_user'),
                'PASSWORD': config('ORACLE_PASSWORD'),
                'HOST': config('ORACLE_HOST', default='localhost'),
                'PORT': config('ORACLE_PORT', default='1521'),
                'OPTIONS': {
                    'threaded': True,
                    'encoding': 'UTF-8',
                },
                'TEST': {
                    'USER': f"test_{config('ORACLE_USER', default='dess_user')}",
                },                'CONN_MAX_AGE': 0,  # No persistent connections with Oracle
            }
        }
    
    def _get_sqlite_config(self):
        """Configuración para SQLite (desarrollo)"""
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': self.base_dir / 'db.sqlite3',
                'OPTIONS': {
                    'timeout': 30,
                },
                'CONN_MAX_AGE': 300,  # Connection pooling for SQLite
            }
        }
    
    def get_connection_info(self):
        """Retorna información de conexión para debugging"""
        if self.engine.lower() == 'oracle':
            return {
                'engine': 'Oracle Database',
                'host': config('ORACLE_HOST', default='localhost'),
                'port': config('ORACLE_PORT', default='1521'),
                'service': config('ORACLE_SERVICE_NAME', default='XEPDB1'),
                'user': config('ORACLE_USER', default='dess_user'),
            }
        else:
            return {
                'engine': 'SQLite',
                'path': str(self.base_dir / 'db.sqlite3'),
            }


# Instancia global del manager
db_manager = DatabaseConfigManager()

# Función de compatibilidad (mantener por ahora)
def get_database_config():
    """Función legacy - usar db_manager.get_database_config() en su lugar"""
    return db_manager.get_database_config()


# ============================================================================
# CONFIGURACIÓN DE TESTING
# ============================================================================

def get_test_database_config():
    """Configuración específica para testing"""
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'OPTIONS': {
                'timeout': 30,
            },
        }
    }


# ============================================================================
# INSTRUCCIONES UNIFICADAS PARA USO
# ============================================================================
"""
CONFIGURACIÓN SIMPLIFICADA DE BASE DE DATOS DESS

1. DESARROLLO (SQLite - por defecto):
   En .env: DATABASE_ENGINE=sqlite
   
2. PRODUCCIÓN/PRUEBAS (Oracle):
   En .env:
   DATABASE_ENGINE=oracle
   ORACLE_HOST=servidor.empresa.com
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=DESS_PROD
   ORACLE_USER=dess_user
   ORACLE_PASSWORD=password_seguro

3. COMANDOS ÚTILES UNIFICADOS:
   # Ver configuración actual
   python manage.py shell -c "from config.database_config import db_manager; print(db_manager.get_connection_info())"
   
   # Setup completo con datos de ejemplo
   python manage.py dess_manage setup
   
   # Solo resetear usuarios (mantener un admin)
   python manage.py dess_manage reset
   
   # Ver estadísticas del sistema
   python manage.py dess_manage stats
"""
