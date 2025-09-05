# DESS - Desarrollador de Ecosistemas de Soluciones Empresariales

## 🎯 Descripción

DESS es una plataforma empresarial completa que centraliza el acceso y gestión de todas las soluciones tecnológicas de la organización. Permite despliegues automatizados multi-framework, administración centralizada de permisos y monitoreo en tiempo real de aplicaciones.

## ✨ Características Principales

- 🎯 **Concentrador Central**: Acceso unificado a todas las soluciones empresariales
- 👥 **Gestión de Usuarios**: Sistema de roles y permisos granular con interfaz administrativa
- 🚀 **Deployment Automatizado**: Deploy multi-framework con detección automática (React, Vue, Django, FastAPI, Flask, etc.)
- 📊 **Dashboard Personalizado**: Vista adaptada según rol y permisos con diseño DESS corporativo
- 🔒 **Seguridad Empresarial**: Autenticación JWT, control de accesos y middlewares de seguridad
- 🐳 **Containerización**: Configuración Docker completa para desarrollo y producción
- 🔗 **Webhooks GitHub**: Deployment automático con push a repositorios
- 📈 **Health Check API**: Monitoreo del estado del sistema
- 🎨 **Sistema de Diseño**: Interfaz consistente con paleta corporativa DESS

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

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11 + Django 4.2 + Django REST Framework
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL/Oracle (producción) 
- **Frontend**: HTML5 + Tailwind CSS + JavaScript vanilla
- **Autenticación**: JWT (JSON Web Tokens) + Session-based
- **API Documentation**: OpenAPI/Swagger (DRF Spectacular)
- **Containerización**: Docker + Docker Compose
- **Archivos Estáticos**: WhiteNoise
- **Testing**: pytest + pytest-django
- **Deployment**: Sistema propio multi-framework

## 🚀 Setup del Proyecto

### Prerequisitos

- Python 3.11+
- Docker Desktop (recomendado)
- Git
- Node.js (para deployments de proyectos JavaScript)

### Instalación Rápida con Docker

```bash
# Clonar repositorio
git clone https://github.com/your-org/dess.git
cd dess

# Levantar con Docker
docker-compose up -d

# Crear superusuario
docker-compose exec dess-app python manage.py createsuperuser
```

### Instalación Local (Desarrollo)

1. **Crear virtual environment**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar migraciones**:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Crear superusuario**:
```bash
python manage.py createsuperuser
```

5. **Ejecutar servidor**:
```bash
python manage.py runserver
```

### Configuración de Producción

Para producción, configurar las siguientes variables de entorno:

```bash
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dess
ALLOWED_HOSTS=yourdomain.com
DOCKER_HOST=unix:///var/run/docker.sock
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

## 🌐 URLs y Endpoints

### Interfaz Web
- **Dashboard Admin**: <http://localhost:8000/admin-panel/dashboard/>
- **Dashboard Usuario**: <http://localhost:8000/dashboard/>
- **Login**: <http://localhost:8000/login/>

### APIs
- **Health Check**: <http://localhost:8000/api/status/>
- **API Docs**: <http://localhost:8000/api/docs/>
- **API Schema**: <http://localhost:8000/api/schema/>
- **Admin Django**: <http://localhost:8000/admin/>

### Deployment APIs
- **Deploy Proyecto**: `POST /api/deployments/{id}/deploy/`
- **Ver Logs**: `GET /api/deployments/{id}/logs/`
- **Detectar Tipo**: `POST /api/deployments/detect-type/`
- **GitHub Webhook**: `POST /webhooks/github/{deployment_id}/`

## 🔧 Funcionalidades Principales

### Sistema de Deployment
- **Detección Automática**: Identifica tipos de proyecto (React, Vue, Django, FastAPI, Flask)
- **Docker Automático**: Genera Dockerfiles optimizados
- **Deployment en Vivo**: Deploy desde repositorios Git
- **Webhooks**: Deployment automático con GitHub
- **Monitoreo**: Logs en tiempo real

### Gestión de Usuarios
- **Roles**: Super Admin y Usuario Regular
- **Permisos**: Control granular de acceso
- **Perfiles**: Gestión de información personal
- **Asignaciones**: Control de acceso a soluciones

### Dashboard Administrativo
- **Estadísticas**: Métricas de usuarios y soluciones
- **Gestión Visual**: Interface moderna con Tailwind CSS
- **Navegación Intuitiva**: Diseño DESS corporativo
- **Responsive**: Compatible con dispositivos móviles

## 🛠️ Desarrollo

### Comandos Útiles

```bash
# Desarrollo local
python manage.py runserver

# Docker development
docker-compose up -d

# Crear migraciones
python manage.py makemigrations

# Ejecutar tests
python manage.py test

# Collectstatic
python manage.py collectstatic

# Logs en Docker
docker-compose logs -f dess-app
```

## 📚 Documentación

- **Documentación Técnica**: `DOCUMENTACION_TECNICA_DESS.md`
- **API Reference**: Disponible en `/api/docs/`
- **Arquitectura**: Clean Architecture implementada
- **Testing**: Suite completa de tests unitarios e integración

## 🤝 Contribución

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo MIT License.

---

**DESS v1.1.0** - Desarrollado con ❤️ para centralizar y automatizar soluciones empresariales.
