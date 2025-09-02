#!/bin/bash
set -e

# Colores para el output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging con colores
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] DESS:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] DESS SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] DESS WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] DESS ERROR:${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    log_error "manage.py not found. Make sure we're in the Django project directory."
    exit 1
fi

# Esperar a que la base de datos esté disponible
wait_for_db() {
    if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" != *"sqlite"* ]]; then
        log "Waiting for database to be ready..."
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connections
from django.db.utils import OperationalError
try:
    connections['default'].cursor()
    print('Database connection successful!')
    sys.exit(0)
except OperationalError as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error: {e}')
    sys.exit(1)
" 2>/dev/null; then
                log_success "Database is ready!"
                break
            else
                log "Database not ready, attempt $attempt/$max_attempts..."
                sleep 2
                attempt=$((attempt + 1))
            fi
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Database failed to become ready after $max_attempts attempts"
            exit 1
        fi
    else
        log "Using SQLite database (no wait needed)"
    fi
}

# Ejecutar migraciones
run_migrations() {
    log "Running database migrations..."
    if python manage.py migrate --noinput; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Crear superusuario si no existe
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
        log "Checking/creating superuser..."
        python manage.py shell -c "
import os
from infrastructure.database.models import DESSUser
try:
    username = os.environ['DJANGO_SUPERUSER_USERNAME']
    password = os.environ['DJANGO_SUPERUSER_PASSWORD']
    email = os.environ['DJANGO_SUPERUSER_EMAIL']
    
    if not DESSUser.objects.filter(username=username).exists():
        user = DESSUser.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='super_admin',
            full_name='Super Administrator'
        )
        print(f'Superuser \"{username}\" created successfully')
    else:
        print(f'Superuser \"{username}\" already exists')
except Exception as e:
    print(f'Error creating superuser: {e}')
    exit(1)
" && log_success "Superuser setup completed"
    else
        log_warning "Superuser environment variables not set. Skipping superuser creation."
    fi
}

# Recolectar archivos estáticos
collect_static() {
    log "Collecting static files..."
    if python manage.py collectstatic --noinput; then
        log_success "Static files collected"
    else
        log_error "Failed to collect static files"
        exit 1
    fi
}

# Verificar la configuración del sistema
check_system() {
    log "Checking system configuration..."
    
    # Verificar variables críticas
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "change-me-in-production" ]; then
        log_warning "SECRET_KEY not set or using default value!"
    fi
    
    # Verificar Docker socket si vamos a hacer despliegues
    if [ -S /var/run/docker.sock ]; then
        log_success "Docker socket is available for deployments"
    else
        log_warning "Docker socket not available. Deployment functionality may be limited."
    fi
    
    # Verificar conectividad a Redis si está configurado
    if [ -n "$REDIS_URL" ] && [[ "$REDIS_URL" != *"redis://redis"* ]]; then
        if python -c "
import redis
import os
try:
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print('Redis connection successful!')
except Exception as e:
    print(f'Redis connection failed: {e}')
" 2>/dev/null; then
            log_success "Redis connection verified"
        else
            log_warning "Redis connection failed"
        fi
    fi
    
    log_success "System check completed"
}

# Función principal
main() {
    log "Starting DESS (Desarrollador de Ecosistemas de Soluciones Empresariales)..."
    log "Version: 1.0.0"
    log "Environment: $([ "$DEBUG" = "True" ] && echo "Development" || echo "Production")"
    
    case "$1" in
        "runserver")
            log "Starting Django development server..."
            wait_for_db
            run_migrations
            create_superuser
            collect_static
            check_system
            log_success "Starting server on 0.0.0.0:8000"
            exec python manage.py runserver 0.0.0.0:8000
            ;;
        "gunicorn")
            log "Starting Gunicorn production server..."
            wait_for_db
            run_migrations
            create_superuser
            collect_static
            check_system
            log_success "Starting Gunicorn server..."
            exec gunicorn config.wsgi:application \
                --bind 0.0.0.0:8000 \
                --workers ${GUNICORN_WORKERS:-3} \
                --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
                --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
                --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
                --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
                --timeout ${GUNICORN_TIMEOUT:-30} \
                --keep-alive ${GUNICORN_KEEPALIVE:-5} \
                --log-level ${GUNICORN_LOG_LEVEL:-info} \
                --access-logfile - \
                --error-logfile - \
                --preload
            ;;
        "migrate")
            log "Running migrations only..."
            wait_for_db
            run_migrations
            log_success "Migration completed"
            ;;
        "shell")
            log "Starting Django shell..."
            exec python manage.py shell
            ;;
        "createsuperuser")
            log "Creating superuser..."
            create_superuser
            log_success "Superuser creation completed"
            ;;
        "collectstatic")
            log "Collecting static files only..."
            collect_static
            log_success "Static files collection completed"
            ;;
        "check")
            log "Running Django system checks..."
            python manage.py check
            check_system
            log_success "System checks completed"
            ;;
        "bash")
            log "Starting bash shell..."
            exec /bin/bash
            ;;
        *)
            log "Running custom command: $@"
            exec "$@"
            ;;
    esac
}

# Manejo de señales para graceful shutdown
cleanup() {
    log "Received shutdown signal, cleaning up..."
    # Aquí puedes agregar lógica de limpieza si es necesaria
    exit 0
}

trap cleanup SIGTERM SIGINT

# Ejecutar función principal con todos los argumentos
main "$@"