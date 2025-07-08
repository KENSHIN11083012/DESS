# DESS - Desarrollador de Ecosistemas de Soluciones Empresariales

## Descripción

DESS es una plataforma empresarial que centraliza el acceso y gestión de todas las soluciones tecnológicas de la organización, permitiendo despliegues automatizados y administración centralizada de permisos.

## Características Principales

- 🎯 **Concentrador Central**: Acceso unificado a todas las soluciones empresariales
- 👥 **Gestión de Usuarios**: Sistema de roles y permisos granular
- 🚀 **Despliegue Automático**: Deploy de aplicaciones con detección automática
- 📊 **Dashboard Personalizado**: Vista adaptada según rol y permisos
- 🔒 **Seguridad Empresarial**: Autenticación JWT y control de accesos

## Arquitectura

El proyecto sigue los principios de **Clean Architecture**:

```text
DESS/
├── core/                    # Entidades y casos de uso (dominio)
│   ├── entities/           # Modelos de dominio
│   ├── use_cases/          # Lógica de negocio
│   └── interfaces/         # Contratos/interfaces
├── application/            # Servicios de aplicación
│   ├── services/          # Servicios de aplicación
│   └── dtos/              # Data Transfer Objects
├── infrastructure/        # Frameworks y drivers externos
│   ├── web/              # Django REST API
│   ├── database/         # Oracle ORM y repositorios
│   └── security/         # Autenticación y autorización
├── config/               # Configuración Django
└── tests/               # Tests unitarios e integración
```

## Tecnologías

- **Backend**: Python 3.11 + Django 4.2 + Django REST Framework
- **Base de Datos**: Oracle Database 19c
- **Autenticación**: JWT (JSON Web Tokens)
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest + pytest-django

## Setup del Proyecto

### Prerequisitos

- Python 3.11+
- Oracle Database 19c (opcional - actualmente usando SQLite)
- Oracle Instant Client (para producción)
- Git

### Instalación

1. **Crear virtual environment**:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

1. **Instalar dependencias**:

**Para desarrollo local (incluye testing y herramientas):**

```bash
pip install -r requirements-dev.txt
```

**Para producción (solo dependencias críticas):**

```bash
pip install -r requirements.txt
```

1. **Configurar variables de entorno**:

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

1. **Configurar Oracle Database** (opcional):
   - Crear usuario DESS en Oracle
   - Configurar permisos necesarios
   - Actualizar credenciales en .env
   - Descomentar cx-Oracle en requirements-dev.txt

1. **Ejecutar migraciones**:

```bash
python manage.py makemigrations
python manage.py migrate
```

1. **Crear superusuario**:

```bash
python manage.py createsuperuser
```

1. **Ejecutar servidor de desarrollo**:

```bash
python manage.py runserver
```

### URLs Importantes

- **API Docs**: <http://localhost:8000/api/docs/>
- **Admin**: <http://localhost:8000/admin/>
- **API Base**: <http://localhost:8000/api/v1/>
- **Dashboard**: <http://localhost:8000/dashboard/>

## Desarrollo

### Estándares de Código

- **Formatting**: Black
- **Linting**: Flake8
- **Import Sorting**: isort
- **Testing**: pytest con cobertura >80%

### Comandos de Desarrollo

```bash
# Formatear código
black .

# Linting
flake8 .

# Tests
pytest

# Cobertura
pytest --cov=core --cov=application --cov=infrastructure

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

## Contribución

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request
