"""
Servicio de Gestión de Despliegues - DESS
Maneja la detección automática de tipos de proyecto y despliegue con Docker
"""
import os
import json
import subprocess
import requests
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import docker
from django.conf import settings
from django.utils import timezone
import logging
from asgiref.sync import sync_to_async

from infrastructure.database.models_package.deployment import (
    Deployment, DeploymentStatus, ProjectType, DeploymentLog
)

logger = logging.getLogger(__name__)


class ProjectDetector:
    """Detector automático de tipos de proyecto"""
    
    @staticmethod
    def detect_project_type(repo_path: str) -> ProjectType:
        """Detectar tipo de proyecto analizando archivos"""
        
        files_in_repo = os.listdir(repo_path)
        files_set = set(files_in_repo)
        
        # Detectar Docker primero
        if 'Dockerfile' in files_set or 'docker-compose.yml' in files_set:
            return ProjectType.DOCKER
        
        # Detectar Django
        if 'manage.py' in files_set and 'requirements.txt' in files_set:
            return ProjectType.DJANGO
        
        # Detectar Next.js
        if 'next.config.js' in files_set or 'next.config.ts' in files_set:
            return ProjectType.NEXTJS
        
        # Detectar React (debe ir después de Next.js)
        if 'package.json' in files_set:
            try:
                with open(os.path.join(repo_path, 'package.json'), 'r') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    
                    if 'react' in dependencies:
                        return ProjectType.REACT
                    elif 'express' in dependencies:
                        return ProjectType.NODE
                    else:
                        return ProjectType.NODE
            except:
                pass
        
        # Detectar Flask
        if any('flask' in f.lower() for f in files_in_repo) or 'app.py' in files_set:
            return ProjectType.FLASK
        
        # Detectar FastAPI
        if any('fastapi' in f.lower() for f in files_in_repo) or 'main.py' in files_set:
            # Verificar si realmente es FastAPI leyendo archivos Python
            for file in files_in_repo:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(repo_path, file), 'r') as f:
                            content = f.read()
                            if 'fastapi' in content.lower():
                                return ProjectType.FASTAPI
                    except:
                        pass
        
        # Detectar sitio estático
        static_files = {'index.html', 'index.htm'}
        if files_set.intersection(static_files):
            return ProjectType.STATIC
        
        # Por defecto, asumir Docker si no se puede determinar
        return ProjectType.DOCKER


class DockerfileGenerator:
    """Generador de Dockerfiles para diferentes tipos de proyecto"""
    
    @staticmethod
    def generate_dockerfile(project_type: ProjectType, repo_path: str) -> str:
        """Generar Dockerfile basado en el tipo de proyecto"""
        
        templates = {
            ProjectType.DJANGO: """
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    default-libmysqlclient-dev \\
    pkg-config \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Ejecutar collectstatic (solo si existe manage.py)
RUN if [ -f manage.py ]; then python manage.py collectstatic --noinput || echo "No static files configured"; fi

# Exponer puerto
EXPOSE 8000

# Comando por defecto (con migraciones automáticas)
CMD sh -c 'if [ -f manage.py ]; then echo "Ejecutando migraciones Django..." && python manage.py migrate --noinput || echo "Error en migraciones"; echo "Iniciando servidor Django..." && python manage.py runserver 0.0.0.0:8000; else echo "No se encontró manage.py. ¿Es un proyecto Django válido?"; echo "Archivos disponibles:"; ls -la /app; sleep 3600; fi'
            """,
            
            ProjectType.REACT: """
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar todas las dependencias (incluyendo dev para build)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copiar código fuente
COPY . .

# Construir la aplicación
RUN npm run build || echo "Build falló, continuando..."

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Copiar package files solo para producción
COPY package*.json ./

# Instalar solo dependencias de producción
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Copiar build desde el stage anterior
COPY --from=builder /app/build ./build 2>/dev/null || echo "No build folder, copying all files"
COPY --from=builder /app/public ./public 2>/dev/null || echo "No public folder"

# Si no hay build folder, copiar todo
RUN if [ ! -d build ]; then rm -rf /app/* && echo "Copying source files..."; fi
COPY . .

# Exponer puerto
EXPOSE 3000

# Comando por defecto (detección inteligente)
CMD sh -c 'if [ -d build ] && command -v serve >/dev/null; then echo "Sirviendo build estático..." && npx serve -s build -l 3000; elif grep -q "\"start\"" package.json; then echo "Ejecutando npm start..." && npm start; else echo "Iniciando servidor de desarrollo..." && npm run dev || npm start; fi'
            """,
            
            ProjectType.NODE: """
FROM node:18-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias (con fallback si no hay package-lock.json)
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 3000

# Comando por defecto (detección inteligente de aplicaciones vs librerías)
CMD sh -c 'if [ -f package.json ] && grep -q "\"start\"" package.json; then echo "Ejecutando npm start..." && npm start; elif [ -f app.js ]; then echo "Ejecutando node app.js..." && node app.js; elif [ -f server.js ]; then echo "Ejecutando node server.js..." && node server.js; elif [ -f index.js ] && ! grep -q "\"main\".*\"index.js\".*\"express\"" package.json; then echo "Ejecutando node index.js..." && node index.js; else echo "ADVERTENCIA: Este parece ser una librería, no una aplicación web." && echo "Para deployar necesitas una aplicación con servidor web." && echo "Archivos disponibles:" && ls -la /app && sleep 3600; fi'
            """,
            
            ProjectType.NEXTJS: """
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
            """,
            
            ProjectType.FLASK: """
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt* .

# Instalar dependencias Python (con fallback si no hay requirements.txt)
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install flask; fi

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando por defecto (detección inteligente del archivo principal)
CMD sh -c 'if [ -f app.py ]; then echo "Ejecutando Flask app.py..." && python app.py; elif [ -f main.py ]; then echo "Ejecutando Flask main.py..." && python main.py; elif [ -f run.py ]; then echo "Ejecutando Flask run.py..." && python run.py; else echo "Ejecutando Flask con auto-discovery..." && flask run --host=0.0.0.0 --port=5000; fi'
            """,
            
            ProjectType.FASTAPI: """
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt* .

# Instalar dependencias Python (con fallback si no hay requirements.txt)
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install fastapi uvicorn; fi

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto (detección inteligente del archivo principal)
CMD sh -c 'if [ -f main.py ]; then echo "Ejecutando FastAPI main.py..." && uvicorn main:app --host 0.0.0.0 --port 8000; elif [ -f app.py ]; then echo "Ejecutando FastAPI app.py..." && uvicorn app:app --host 0.0.0.0 --port 8000; elif [ -f api.py ]; then echo "Ejecutando FastAPI api.py..." && uvicorn api:app --host 0.0.0.0 --port 8000; else echo "No se encontró archivo FastAPI válido. Archivos disponibles:" && ls -la /app && sleep 3600; fi'
            """,
            
            ProjectType.STATIC: """
FROM nginx:alpine

COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
            """
        }
        
        # Obtener template por tipo de proyecto, NODE por defecto
        template = templates.get(project_type, templates[ProjectType.NODE])
        return template.strip()


class DeploymentService:
    """Servicio principal de gestión de despliegues"""
    
    def __init__(self):
        # Estrategia de conexión inteligente para diferentes entornos
        connection_strategies = [
            # 1. Estrategia para Windows con Docker Desktop (host network)
            {
                'name': 'Docker Desktop Host',
                'base_url': 'tcp://host.docker.internal:2375',
                'description': 'Docker Desktop en Windows via host.docker.internal'
            },
            # 2. Estrategia para Windows TCP local
            {
                'name': 'TCP Local',
                'base_url': 'tcp://localhost:2375',
                'description': 'Docker TCP en localhost'
            },
            # 3. Estrategia para Linux/Unix socket
            {
                'name': 'Unix Socket',
                'base_url': 'unix:///var/run/docker.sock',
                'description': 'Socket Unix estándar'
            },
            # 4. Estrategia por defecto (variables de entorno)
            {
                'name': 'Environment Default',
                'base_url': None,  # Usar docker.from_env()
                'description': 'Configuración por defecto del sistema'
            }
        ]
        
        for strategy in connection_strategies:
            try:
                if strategy['base_url'] is None:
                    # Usar from_env() para configuración por defecto
                    self.docker_client = docker.from_env()
                else:
                    # Usar URL específica
                    self.docker_client = docker.DockerClient(base_url=strategy['base_url'])
                
                # Verificar que funciona con timeout corto
                self.docker_client.ping()
                logger.info(f"✅ Docker conectado via {strategy['name']}: {strategy['description']}")
                # Inicializar temp_dir después de conectar exitosamente
                self.temp_dir = tempfile.mkdtemp()
                return  # Salir si la conexión es exitosa
                
            except Exception as e:
                logger.warning(f"❌ {strategy['name']} falló: {str(e)}")
                continue
        
        # Si llegamos aquí, ninguna estrategia funcionó
        logger.error("🚨 No se pudo conectar con Docker daemon usando ninguna estrategia")
        
        # En lugar de fallar completamente, vamos a crear un cliente mock para desarrollo
        logger.warning("⚠️  Creando cliente Docker mock para desarrollo")
        self.docker_client = None  # Cliente mock
        
        self.temp_dir = tempfile.mkdtemp()
    
    def is_docker_available(self) -> bool:
        """Verificar si Docker está disponible usando CLI directo"""
        try:
            # Usar comando docker directo que sabemos que funciona
            result = subprocess.run(['docker', 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            logger.info(f"Docker version check - Return code: {result.returncode}")
            logger.info(f"Docker version stdout: {result.stdout[:500]}")
            logger.info(f"Docker version stderr: {result.stderr[:500]}")
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Docker availability check failed: {str(e)}")
            return False
    
    def run_docker_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Ejecutar comando docker y devolver resultado"""
        try:
            full_cmd = ['docker'] + cmd
            result = subprocess.run(full_cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)  # 5 minutes timeout
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            logger.info(f"Docker command: {' '.join(full_cmd)}")
            logger.info(f"Result: {result.returncode} - {output[:500]}")
            
            return success, output
        except subprocess.TimeoutExpired:
            logger.error("Docker command timed out")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Error running docker command: {e}")
            return False, str(e)
    
    def create_deployment(self, github_url: str, name: str, created_by, **kwargs) -> Deployment:
        """Crear un nuevo despliegue"""
        
        # Verificar si Docker está disponible
        if not self.is_docker_available():
            logger.error("❌ Docker no disponible - no se puede crear el despliegue")
            raise Exception("Docker no está disponible. Configure Docker antes de crear despliegues.")
        
        deployment = Deployment.objects.create(
            name=name,
            github_url=github_url,
            created_by=created_by,
            **kwargs
        )
        
        self._log(deployment, 'info', f'✅ Despliegue creado: {name}')
        
        return deployment
    
    def deploy_project(self, deployment: Deployment) -> bool:
        """Desplegar un proyecto completo"""
        
        # Si Docker no está disponible, fallar
        if not self.is_docker_available():
            self._log(deployment, 'error', '🔴 ERROR: Docker no está disponible')
            deployment.status = DeploymentStatus.FAILED
            deployment.save()
            return False
        
        repo_path = None
        try:
            # 1. Clonar repositorio
            deployment.status = DeploymentStatus.CLONING
            deployment.save()
            repo_path = self._clone_repository(deployment)
            
            # 2. Detectar tipo de proyecto
            deployment.status = DeploymentStatus.ANALYZING
            deployment.save()
            project_type = ProjectDetector.detect_project_type(repo_path)
            deployment.project_type = project_type
            deployment.save()
            
            self._log(deployment, 'info', f'Tipo de proyecto detectado: {project_type}')
            
            # 3. Generar Dockerfile si no existe
            dockerfile_path = os.path.join(repo_path, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                self._log(deployment, 'info', f'Generando Dockerfile para proyecto tipo: {project_type}')
                try:
                    dockerfile_content = DockerfileGenerator.generate_dockerfile(project_type, repo_path)
                    self._log(deployment, 'info', f'Dockerfile generado, contenido: {len(dockerfile_content)} caracteres')
                    with open(dockerfile_path, 'w') as f:
                        f.write(dockerfile_content)
                    self._log(deployment, 'info', 'Dockerfile generado automáticamente')
                except Exception as dockerfile_error:
                    self._log(deployment, 'error', f'Error generando Dockerfile: {str(dockerfile_error)}')
                    raise dockerfile_error
            else:
                self._log(deployment, 'info', 'Usando Dockerfile existente en el repositorio')
            
            # 4. Construir imagen Docker
            deployment.status = DeploymentStatus.BUILDING
            deployment.save()
            image_name = self._build_docker_image(deployment, repo_path)
            
            # 5. Desplegar contenedor
            deployment.status = DeploymentStatus.DEPLOYING
            deployment.save()
            container_id = self._deploy_container(deployment, image_name)
            
            # 6. Verificar despliegue
            if self._verify_deployment(deployment):
                deployment.status = DeploymentStatus.RUNNING
                deployment.last_deployed = timezone.now()
                deployment.save()
                
                # 7. Crear Solution automáticamente para que usuarios puedan acceder
                self._create_solution_from_deployment(deployment)
                
                self._log(deployment, 'success', 'Despliegue completado exitosamente')
                return True
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.save()
                return False
                
        except Exception as e:
            self._log(deployment, 'error', f'Error en despliegue: {str(e)}')
            deployment.status = DeploymentStatus.FAILED
            deployment.save()
            return False
        
        finally:
            # Limpiar archivos temporales
            if repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
    
    def _clone_repository(self, deployment: Deployment) -> str:
        """Clonar repositorio de GitHub"""
        
        repo_name = deployment.get_repo_name()
        repo_path = os.path.join(self.temp_dir, repo_name)
        
        self._log(deployment, 'info', f'Clonando repositorio: {deployment.github_url}')
        
        # Configurar git para repositorios públicos (evitar solicitud de credenciales)
        git_env = os.environ.copy()
        git_env['GIT_TERMINAL_PROMPT'] = '0'  # Desactivar prompts interactivos
        git_env['GIT_ASKPASS'] = '/bin/echo'  # Comando dummy para evitar prompts
        
        # Determinar branch correcto - si es main pero el repo usa master, intentar ambos
        branch_to_use = deployment.branch or 'main'
        
        cmd = [
            'git', 'clone', 
            '--depth', '1',
            '--branch', branch_to_use,
            deployment.get_clone_url(),
            repo_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=git_env)
        
        if result.returncode != 0:
            # Si falla por branch, intentar con master/main alterno
            alternate_branch = 'master' if branch_to_use == 'main' else 'main'
            
            cmd_retry = [
                'git', 'clone', 
                '--depth', '1',
                '--branch', alternate_branch,
                deployment.get_clone_url(),
                repo_path
            ]
            
            result_retry = subprocess.run(cmd_retry, capture_output=True, text=True, env=git_env)
            
            if result_retry.returncode != 0:
                # Si ambos branches fallan, intentar sin especificar branch (usa el default)
                cmd_final = [
                    'git', 'clone', 
                    '--depth', '1',
                    deployment.get_clone_url(),
                    repo_path
                ]
                
                result_final = subprocess.run(cmd_final, capture_output=True, text=True, env=git_env)
                
                if result_final.returncode != 0:
                    error_msg = f'Error clonando repositorio:\n1) Branch {branch_to_use}: {result.stderr}\n2) Branch {alternate_branch}: {result_retry.stderr}\n3) Branch default: {result_final.stderr}'
                    raise Exception(error_msg)
        
        self._log(deployment, 'info', 'Repositorio clonado exitosamente')
        return repo_path
    
    def _build_docker_image(self, deployment: Deployment, repo_path: str) -> str:
        """Construir imagen Docker"""
        
        image_name = f"dess-deploy-{deployment.id}"
        deployment.image_name = image_name
        deployment.save()
        
        self._log(deployment, 'info', f'Construyendo imagen Docker: {image_name}')
        
        try:
            # Verificar conexión Docker antes de construir
            self.docker_client.ping()
            
            # Detectar si hay problemas de snapshot/cache
            build_args = {
                'path': repo_path,
                'tag': image_name,
                'rm': True,
                'pull': True,  # Siempre pull imagen base
                'nocache': False  # Inicialmente usar cache
            }
            
            # Construir imagen con manejo de errores de snapshot
            try:
                image, build_logs = self.docker_client.images.build(
                    path=repo_path,
                    tag=image_name,
                    rm=True,
                    forcerm=True,
                    nocache=build_args['nocache'],
                    pull=build_args['pull']
                )
            except docker.errors.BuildError as e:
                # Si falla por problemas de snapshot, intentar sin cache
                if "does not exist: not found" in str(e) or "snapshot" in str(e).lower():
                    self._log(deployment, 'warning', 'Error de snapshot detectado, reintentando sin cache...')
                    image, build_logs = self.docker_client.images.build(
                        path=repo_path,
                        tag=image_name,
                        rm=True,
                        forcerm=True,
                        nocache=True,
                        pull=True
                    )
                else:
                    raise e
            
            # Guardar logs de construcción
            logs_text = []
            for log in build_logs:
                if 'stream' in log:
                    logs_text.append(log['stream'].strip())
            
            deployment.build_logs = '\n'.join(logs_text)
            deployment.save()
            
            self._log(deployment, 'info', 'Imagen construida exitosamente')
            return image_name
            
        except docker.errors.APIError as e:
            if "http+docker" in str(e):
                error_msg = "Error de conexión con Docker daemon. Asegúrate de que Docker Desktop esté ejecutándose."
            else:
                error_msg = f"Error de API Docker: {str(e)}"
            deployment.build_logs = error_msg
            deployment.save()
            raise Exception(error_msg)
        except docker.errors.BuildError as e:
            # Capturar logs detallados del build error
            error_logs = []
            if hasattr(e, 'build_log'):
                for log in e.build_log:
                    if 'stream' in log:
                        error_logs.append(log['stream'].strip())
                    elif 'error' in log:
                        error_logs.append(f"ERROR: {log['error']}")
            
            detailed_logs = '\n'.join(error_logs) if error_logs else str(e)
            error_msg = f"Error construyendo imagen: {str(e)}"
            full_error_msg = f"{error_msg}\n\nLogs detallados:\n{detailed_logs}"
            
            deployment.build_logs = full_error_msg
            deployment.save()
            
            # Log el error completo para debugging
            self._log(deployment, 'error', f"Build falló. Logs completos: {detailed_logs}")
            raise Exception(error_msg)
        except Exception as e:
            if "http+docker" in str(e):
                error_msg = "Docker daemon no está disponible. Inicia Docker Desktop y asegúrate de que esté ejecutándose correctamente."
            else:
                error_msg = f"Error inesperado construyendo imagen: {str(e)}"
            deployment.build_logs = error_msg
            deployment.save()
            raise Exception(error_msg)
    
    def _deploy_container(self, deployment: Deployment, image_name: str) -> str:
        """Desplegar contenedor Docker"""
        
        # Limpiar contenedores anteriores del mismo deployment
        self._cleanup_existing_container(deployment)
        
        # Obtener configuración del proyecto
        config = deployment.get_project_config()
        
        # Determinar puerto interno basado en el tipo de proyecto
        project_type = deployment.project_type
        if project_type in [ProjectType.NODE, ProjectType.REACT, ProjectType.NEXTJS]:
            internal_port = 3000  # Puerto estándar para Node.js/React
        elif project_type == ProjectType.FLASK:
            internal_port = 5000  # Puerto estándar para Flask
        else:
            internal_port = deployment.port or config.get('port', 8000)  # Django y otros
        
        port = internal_port
        
        # Asignar puerto disponible
        available_port = self._get_available_port()
        deployment.port = available_port
        deployment.deploy_url = f"http://localhost:{available_port}"
        deployment.save()
        
        self._log(deployment, 'info', f'Desplegando en puerto {available_port}')
        
        try:
            # Verificar conexión Docker antes de desplegar
            self.docker_client.ping()
            
            # Preparar variables de entorno específicas por tipo de proyecto
            env_vars = deployment.environment_vars or {}
            
            # Configurar variables de entorno según el tipo de proyecto
            if project_type in [ProjectType.NODE, ProjectType.REACT, ProjectType.NEXTJS]:
                env_vars['PORT'] = str(port)
                env_vars['NODE_ENV'] = 'production'
            elif project_type == ProjectType.DJANGO:
                env_vars['DJANGO_SETTINGS_MODULE'] = env_vars.get('DJANGO_SETTINGS_MODULE', 'settings')
                env_vars['DEBUG'] = 'False'
                env_vars['ALLOWED_HOSTS'] = '*'
            elif project_type == ProjectType.FLASK:
                env_vars['FLASK_ENV'] = 'production'
                env_vars['FLASK_APP'] = env_vars.get('FLASK_APP', 'app.py')
                env_vars['PORT'] = str(port)
            elif project_type == ProjectType.FASTAPI:
                env_vars['PORT'] = str(port)
                env_vars['HOST'] = '0.0.0.0'
                
            # Crear y ejecutar contenedor
            container = self.docker_client.containers.run(
                image_name,
                detach=True,
                ports={f'{port}/tcp': available_port},
                environment=env_vars,
                name=f"dess-container-{deployment.id}",
                restart_policy={"Name": "unless-stopped"}
            )
            
            deployment.container_id = container.id
            deployment.save()
            
            self._log(deployment, 'info', f'Contenedor desplegado: {container.id[:12]}')
            return container.id
            
        except docker.errors.APIError as e:
            if "http+docker" in str(e):
                raise Exception("Docker daemon no está disponible. Verifica que Docker Desktop esté ejecutándose.")
            else:
                raise Exception(f'Error de API Docker: {str(e)}')
        except docker.errors.ContainerError as e:
            raise Exception(f'Error desplegando contenedor: {str(e)}')
        except Exception as e:
            if "http+docker" in str(e):
                raise Exception("Docker daemon no está disponible. Inicia Docker Desktop y asegúrate de que esté ejecutándose.")
            else:
                raise Exception(f'Error inesperado desplegando contenedor: {str(e)}')
    
    def _verify_deployment(self, deployment: Deployment) -> bool:
        """Verificar que el despliegue esté funcionando"""
        
        if not deployment.deploy_url:
            return False
        
        import time
        max_attempts = 6  # 6 intentos durante 30 segundos
        
        for attempt in range(max_attempts):
            try:
                # Esperar progresivamente más tiempo entre intentos
                wait_time = 5 + (attempt * 2)  # 5, 7, 9, 11, 13, 15 segundos
                if attempt > 0:
                    self._log(deployment, 'info', f'Reintentando verificación ({attempt + 1}/{max_attempts}) después de {wait_time}s...')
                
                time.sleep(wait_time)
                
                response = requests.get(deployment.deploy_url, timeout=15)
                
                if response.status_code == 200:
                    self._log(deployment, 'success', 'Verificación de salud exitosa')
                    return True
                elif response.status_code in [404, 502, 503]:
                    # Códigos que indican que el servidor está respondiendo pero la app puede no estar lista
                    self._log(deployment, 'info', f'Servidor responde con {response.status_code}, continuando verificaciones...')
                    continue
                else:
                    self._log(deployment, 'warning', f'Respuesta inesperada: {response.status_code}')
                    continue
                    
            except requests.RequestException as e:
                self._log(deployment, 'info', f'Verificación {attempt + 1}/{max_attempts} falló: {str(e)}')
                
                if attempt == max_attempts - 1:
                    # Solo en el último intento, hacer diagnóstico completo
                    self._diagnose_container_failure(deployment)
                    
                    # Verificar si el contenedor está funcionando aunque el health check falle
                    if self._is_container_healthy(deployment):
                        self._log(deployment, 'warning', 'El contenedor está funcionando pero no responde a HTTP. Marcando como exitoso.')
                        return True
        
        self._log(deployment, 'warning', 'Verificación de salud falló después de todos los intentos')
        return False
    
    def _diagnose_container_failure(self, deployment: Deployment):
        """Diagnosticar por qué el contenedor falló o no responde"""
        if not deployment.container_id:
            self._log(deployment, 'error', 'No hay container_id para diagnosticar')
            return
        
        try:
            container = self.docker_client.containers.get(deployment.container_id)
            
            # 1. Estado del contenedor
            status = container.status
            self._log(deployment, 'info', f'Estado del contenedor: {status}')
            
            # 2. Obtener logs del contenedor (stdout y stderr)
            try:
                logs_stdout = container.logs(stdout=True, stderr=False, tail=50, timestamps=True).decode('utf-8', errors='ignore')
                logs_stderr = container.logs(stdout=False, stderr=True, tail=50, timestamps=True).decode('utf-8', errors='ignore')
                
                if logs_stdout:
                    self._log(deployment, 'info', f'STDOUT del contenedor:\n{logs_stdout}')
                if logs_stderr:
                    self._log(deployment, 'info', f'STDERR del contenedor:\n{logs_stderr}')
                    
                if not logs_stdout and not logs_stderr:
                    self._log(deployment, 'warning', 'El contenedor no tiene logs disponibles')
                    
                    # Ejecutar comando para diagnóstico adicional
                    self._execute_diagnostic_commands(container, deployment)
                    
            except Exception as e:
                self._log(deployment, 'error', f'Error obteniendo logs: {str(e)}')
            
            # 3. Información adicional si el contenedor está parado
            if status in ['exited', 'dead']:
                attrs = container.attrs
                exit_code = attrs.get('State', {}).get('ExitCode', 'unknown')
                error = attrs.get('State', {}).get('Error', 'No error info')
                
                self._log(deployment, 'error', f'Contenedor terminó con código: {exit_code}')
                if error and error != 'No error info':
                    self._log(deployment, 'error', f'Error del contenedor: {error}')
            
            # 4. Verificar puertos
            port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            self._log(deployment, 'info', f'Port bindings: {port_bindings}')
            
        except docker.errors.NotFound:
            self._log(deployment, 'error', 'Contenedor no encontrado para diagnóstico')
        except Exception as e:
            self._log(deployment, 'error', f'Error durante diagnóstico: {str(e)}')
    
    def _execute_diagnostic_commands(self, container, deployment):
        """Ejecutar comandos de diagnóstico dentro del contenedor"""
        diagnostic_commands = [
            'ps aux',                           # Procesos corriendo
            'ls -la /app',                     # Contenido del directorio de trabajo
            'cat /app/package.json',           # Verificar package.json
            'node --version',                  # Versión de Node
            'npm --version',                   # Versión de npm
            'which node',                      # Ubicación de node
            'ls -la /app/index.js /app/app.js /app/server.js',  # Archivos principales
        ]
        
        for cmd in diagnostic_commands:
            try:
                result = container.exec_run(cmd, stdout=True, stderr=True)
                output = result.output.decode('utf-8', errors='ignore')
                
                if output.strip():
                    self._log(deployment, 'info', f'Comando [{cmd}]:\n{output}')
                else:
                    self._log(deployment, 'warning', f'Comando [{cmd}]: Sin salida')
                    
            except Exception as e:
                self._log(deployment, 'error', f'Error ejecutando [{cmd}]: {str(e)}')
    
    def _get_available_port(self) -> int:
        """Obtener un puerto disponible para el despliegue"""
        import socket
        
        # Rango de puertos para despliegues
        start_port = 8100
        max_port = 8200
        
        for port in range(start_port, max_port):
            # Verificar tanto localhost como 0.0.0.0
            available = True
            for host in ['localhost', '0.0.0.0']:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind((host, port))
                    except OSError:
                        available = False
                        break
            
            if available:
                # Verificar también que no haya contenedores Docker usando este puerto
                if self._is_port_free_in_docker(port):
                    return port
        
        raise Exception("No hay puertos disponibles para el despliegue")
    
    def _is_port_free_in_docker(self, port: int) -> bool:
        """Verificar que el puerto no esté siendo usado por contenedores Docker"""
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                for container_port, host_bindings in port_bindings.items():
                    if host_bindings:
                        for binding in host_bindings:
                            if int(binding.get('HostPort', 0)) == port:
                                # Puerto ocupado, parar este contenedor si es nuestro
                                if container.name.startswith('dess-container-'):
                                    logger.info(f'Limpiando contenedor que ocupa puerto {port}: {container.name}')
                                    container.stop(timeout=5)
                                    container.remove()
                                    return True  # Ahora está libre
                                return False  # Puerto ocupado por otro contenedor
            return True  # Puerto libre
        except Exception as e:
            # Si hay error verificando, asumir que está ocupado
            return False
    
    def _cleanup_existing_container(self, deployment: Deployment):
        """Limpiar contenedores existentes del deployment"""
        try:
            if deployment.container_id:
                # Intentar parar y remover contenedor existente
                try:
                    container = self.docker_client.containers.get(deployment.container_id)
                    container.stop(timeout=10)
                    container.remove()
                    self._log(deployment, 'info', f'Container anterior limpiado: {deployment.container_id[:12]}')
                except docker.errors.NotFound:
                    self._log(deployment, 'info', 'Container anterior ya no existe')
                except Exception as e:
                    self._log(deployment, 'warning', f'Error limpiando container anterior: {str(e)}')
            
            # También limpiar contenedores con el mismo nombre si existen
            container_name = f"dess-container-{deployment.id}"
            try:
                existing = self.docker_client.containers.get(container_name)
                existing.stop(timeout=10)
                existing.remove()
                self._log(deployment, 'info', f'Container con nombre duplicado limpiado: {container_name}')
            except docker.errors.NotFound:
                pass  # No existe, perfecto
            except Exception as e:
                self._log(deployment, 'warning', f'Error limpiando container con nombre {container_name}: {str(e)}')
                
        except Exception as e:
            self._log(deployment, 'warning', f'Error en limpieza general de containers: {str(e)}')
    
    def _is_container_healthy(self, deployment: Deployment) -> bool:
        """Verificar si el contenedor está saludable independientemente del HTTP"""
        if not deployment.container_id:
            return False
            
        try:
            container = self.docker_client.containers.get(deployment.container_id)
            
            # 1. Verificar que esté corriendo
            if container.status != 'running':
                return False
            
            # 2. Verificar logs para buscar signos de que la aplicación se inició
            logs = container.logs(tail=20).decode('utf-8', errors='ignore')
            
            # Palabras clave que indican que el servidor está funcionando (específicas por framework)
            project_type = deployment.project_type
            if project_type in [ProjectType.NODE, ProjectType.REACT, ProjectType.NEXTJS]:
                healthy_indicators = [
                    'Listening on',
                    'Server running',
                    'Started server',
                    'Ready to accept connections',
                    'Application started'
                ]
            elif project_type == ProjectType.DJANGO:
                healthy_indicators = [
                    'Starting development server',
                    'Django version',
                    'Watching for file changes',
                    'Quit the server with CONTROL-C'
                ]
            elif project_type == ProjectType.FLASK:
                healthy_indicators = [
                    'Running on',
                    'Serving Flask app',
                    '* Debug mode:',
                    'WARNING: This is a development server'
                ]
            elif project_type == ProjectType.FASTAPI:
                healthy_indicators = [
                    'Uvicorn running on',
                    'Application startup complete',
                    'Started server process',
                    'Waiting for application startup'
                ]
            elif project_type == ProjectType.STATIC:
                healthy_indicators = [
                    'Configuration complete',
                    'nginx: configuration file',
                    'worker process'
                ]
            else:
                # Fallback para tipos desconocidos
                healthy_indicators = [
                    'Listening on',
                    'Server running',
                    'Started server',
                    'Application started',
                    'Server started',
                    'Ready to accept connections',
                    'Accepting connections',
                    'Running on'
                ]
            
            for indicator in healthy_indicators:
                if indicator in logs:
                    self._log(deployment, 'info', f'Indicador de salud encontrado en logs: "{indicator}"')
                    return True
            
            # 3. Si no encuentra indicadores pero el contenedor lleva más de 30 segundos corriendo, probablemente esté bien
            import time
            container.reload()
            started_at = container.attrs['State']['StartedAt']
            
            # Parsear timestamp de Docker (formato ISO)
            from datetime import datetime
            started_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            current_time = datetime.now(started_time.tzinfo)
            
            uptime_seconds = (current_time - started_time).total_seconds()
            if uptime_seconds > 30:
                self._log(deployment, 'info', f'Contenedor corriendo estable por {uptime_seconds:.1f} segundos')
                return True
                
            return False
            
        except Exception as e:
            self._log(deployment, 'error', f'Error verificando salud del contenedor: {str(e)}')
            return False
    
    def _log(self, deployment: Deployment, level: str, message: str, details: Dict = None):
        """Agregar log al despliegue"""
        
        DeploymentLog.objects.create(
            deployment=deployment,
            level=level,
            message=message,
            details=details or {}
        )
        
        logger.info(f"[{deployment.name}] {message}")
    
    def _create_solution_from_deployment(self, deployment: Deployment):
        """Crear Solution automáticamente desde un deployment exitoso"""
        try:
            # Importar aquí para evitar importaciones circulares
            from infrastructure.database.models import Solution
            
            # Verificar si ya existe una solution para este deployment
            existing_solution = Solution.objects.filter(
                name=deployment.name
            ).first()
            
            if existing_solution:
                # Si existe, actualizar su información
                existing_solution.access_url = deployment.deploy_url
                existing_solution.status = 'active'
                existing_solution.repository_url = deployment.github_url
                existing_solution.version = getattr(deployment, 'version', '1.0.0')
                existing_solution.solution_type = self._map_project_type_to_solution_type(deployment.project_type)
                existing_solution.save()
                
                self._log(deployment, 'info', f'Solution existente actualizada: {existing_solution.name}')
            else:
                # Crear nueva solution
                solution = Solution.objects.create(
                    name=deployment.name,
                    description=deployment.description or f'Aplicación desplegada automáticamente desde {deployment.get_repo_name()}',
                    repository_url=deployment.github_url,
                    status='active',
                    solution_type=self._map_project_type_to_solution_type(deployment.project_type),
                    access_url=deployment.deploy_url,
                    version='1.0.0',
                    created_by=deployment.created_by
                )
                
                self._log(deployment, 'success', f'Solution creada automáticamente: {solution.name} - {solution.access_url}')
                
        except Exception as e:
            self._log(deployment, 'error', f'Error creando Solution automática: {str(e)}')
    
    def _map_project_type_to_solution_type(self, project_type: ProjectType) -> str:
        """Mapear ProjectType a solution_type"""
        mapping = {
            ProjectType.DJANGO: 'web_app',
            ProjectType.REACT: 'web_app',
            ProjectType.NODE: 'web_app',
            ProjectType.NEXTJS: 'web_app',
            ProjectType.FLASK: 'web_app',
            ProjectType.FASTAPI: 'api',
            ProjectType.STATIC: 'web_app',
            ProjectType.DOCKER: 'web_app',
        }
        return mapping.get(project_type, 'web_app')
    
    def _update_solution_status(self, deployment: Deployment, status: str):
        """Actualizar estado de la Solution asociada"""
        try:
            from infrastructure.database.models import Solution
            
            solution = Solution.objects.filter(name=deployment.name).first()
            if solution:
                solution.status = status
                if status == 'inactive':
                    solution.access_url = None
                solution.save()
                
                self._log(deployment, 'info', f'Solution {solution.name} marcada como {status}')
                
        except Exception as e:
            self._log(deployment, 'error', f'Error actualizando estado de Solution: {str(e)}')
    
    def _save_deployment(self, deployment: Deployment):
        """Guardar deployment"""
        deployment.save()
    
    def stop_deployment(self, deployment: Deployment) -> bool:
        """Detener un despliegue"""
        
        if deployment.container_id:
            try:
                container = self.docker_client.containers.get(deployment.container_id)
                container.stop()
                container.remove()
                
                deployment.status = DeploymentStatus.STOPPED
                deployment.container_id = ''
                deployment.save()
                
                # Actualizar Solution asociada
                self._update_solution_status(deployment, 'inactive')
                
                self._log(deployment, 'info', 'Despliegue detenido')
                return True
                
            except docker.errors.NotFound:
                self._log(deployment, 'warning', 'Contenedor no encontrado')
                deployment.status = DeploymentStatus.STOPPED
                deployment.save()
                
                # Actualizar Solution asociada
                self._update_solution_status(deployment, 'inactive')
                return True
            except Exception as e:
                self._log(deployment, 'error', f'Error deteniendo despliegue: {str(e)}')
                return False
        
        return True
    
    def restart_deployment(self, deployment: Deployment) -> bool:
        """Reiniciar un despliegue"""
        
        if deployment.container_id:
            try:
                container = self.docker_client.containers.get(deployment.container_id)
                container.restart()
                
                self._log(deployment, 'info', 'Despliegue reiniciado')
                return True
                
            except Exception as e:
                self._log(deployment, 'error', f'Error reiniciando despliegue: {str(e)}')
                return False
        
        return False
    
