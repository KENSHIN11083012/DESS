# Dockerfile para DESS - Desarrollador de Ecosistemas de Soluciones Empresariales
FROM python:3.11-slim

# Etiquetas de metadatos
LABEL maintainer="DESS Team"
LABEL description="Sistema de gestión y despliegue automatizado de soluciones empresariales"
LABEL version="1.0.0"
LABEL org.opencontainers.image.title="DESS"
LABEL org.opencontainers.image.description="Desarrollador de Ecosistemas de Soluciones Empresariales"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="DESS Team"

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV DEBIAN_FRONTEND=noninteractive

# Crear usuario no-root desde el inicio para seguridad
# Agregar usuario dess al grupo docker para acceso al socket de Docker
RUN groupadd --gid 1000 dess \
    && useradd --uid 1000 --gid dess --shell /bin/bash --create-home dess \
    && groupadd docker \
    && usermod -aG docker dess

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Dependencias básicas
        build-essential \
        git \
        curl \
        wget \
        gnupg2 \
        apt-transport-https \
        ca-certificates \
        # Dependencias para PostgreSQL
        libpq-dev \
        # Dependencias para compilar algunas librerías Python
        gcc \
        g++ \
        make \
        # Utilidades del sistema
        procps \
        vim \
        tree \
    && rm -rf /var/lib/apt/lists/*

# Instalar Docker CLI estático (más confiable que el repositorio)
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-26.1.3.tgz \
    && tar xzvf docker-26.1.3.tgz --strip 1 -C /usr/local/bin docker/docker \
    && rm docker-26.1.3.tgz \
    && chmod +x /usr/local/bin/docker

# Instalar Node.js (para proyectos que lo necesiten en despliegues)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requirements primero para aprovechar el caché de Docker
COPY requirements.txt .

# Actualizar pip y instalar dependencias Python
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/logs /app/media /app/static /app/temp \
    && chown -R dess:dess /app

# Cambiar a usuario no-root
USER dess

# Copiar código fuente del proyecto
COPY --chown=dess:dess . .

# Asegurar que los directorios tengan los permisos correctos
RUN chmod +x /app/docker-entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Health check mejorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/status/ || python -c "import requests; requests.get('http://localhost:8000/api/status/')" || exit 1

# Variables de entorno por defecto
ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
ENV SECRET_KEY=change-me-in-production
ENV DATABASE_URL=sqlite:///app/db.sqlite3
ENV REDIS_URL=redis://redis:6379/0

# Punto de entrada
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando por defecto (puede ser sobreescrito)
CMD ["runserver"]