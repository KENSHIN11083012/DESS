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
import random
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

# Ejecutar collectstatic
RUN python manage.py collectstatic --noinput || echo "No static files"

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
            """,
            
            ProjectType.REACT: """
FROM node:18-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código fuente
COPY . .

# Construir la aplicación
RUN npm run build

# Exponer puerto
EXPOSE 3000

# Comando por defecto
CMD ["npm", "start"]
            """,
            
            ProjectType.NODE: """
FROM node:18-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 3000

# Comando por defecto
CMD ["npm", "start"]
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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
            """,
            
            ProjectType.FASTAPI: """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
            """,
            
            ProjectType.STATIC: """
FROM nginx:alpine

COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
            """
        }
        
        return templates.get(project_type, templates[ProjectType.DOCKER]).strip()


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
        """Verificar si Docker está disponible"""
        return self.docker_client is not None
    
    def create_deployment(self, github_url: str, name: str, created_by, **kwargs) -> Deployment:
        """Crear un nuevo despliegue"""
        
        # Verificar si Docker está disponible
        if not self.is_docker_available():
            logger.warning("⚠️  Docker no disponible - creando despliegue en modo simulación")
            # Crear el despliegue pero con estado de advertencia
            kwargs['status'] = 'pending'
            kwargs['deploy_logs'] = 'MODO SIMULACIÓN: Docker daemon no disponible. Configure Docker TCP (puerto 2375) o ejecute en Linux para usar Docker real.'
        
        deployment = Deployment.objects.create(
            name=name,
            github_url=github_url,
            created_by=created_by,
            **kwargs
        )
        
        if self.is_docker_available():
            self._log(deployment, 'info', f'✅ Despliegue creado: {name}')
        else:
            self._log(deployment, 'warning', f'⚠️  Despliegue creado en modo simulación: {name} - Docker no disponible')
        
        return deployment
    
    async def deploy_project(self, deployment: Deployment) -> bool:
        """Desplegar un proyecto completo"""
        
        # Si Docker no está disponible, usar modo simulación
        if not self.is_docker_available():
            return await self._deploy_project_simulation(deployment)
        
        try:
            # 1. Clonar repositorio
            deployment.status = DeploymentStatus.CLONING
            deployment.save()
            repo_path = await self._clone_repository(deployment)
            
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
                dockerfile_content = DockerfileGenerator.generate_dockerfile(project_type, repo_path)
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                self._log(deployment, 'info', 'Dockerfile generado automáticamente')
            
            # 4. Construir imagen Docker
            deployment.status = DeploymentStatus.BUILDING
            deployment.save()
            image_name = await self._build_docker_image(deployment, repo_path)
            
            # 5. Desplegar contenedor
            deployment.status = DeploymentStatus.DEPLOYING
            deployment.save()
            container_id = await self._deploy_container(deployment, image_name)
            
            # 6. Verificar despliegue
            if await self._verify_deployment(deployment):
                deployment.status = DeploymentStatus.RUNNING
                deployment.last_deployed = timezone.now()
                deployment.save()
                
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
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
    
    async def _clone_repository(self, deployment: Deployment) -> str:
        """Clonar repositorio de GitHub"""
        
        repo_name = deployment.get_repo_name()
        repo_path = os.path.join(self.temp_dir, repo_name)
        
        self._log(deployment, 'info', f'Clonando repositorio: {deployment.github_url}')
        
        cmd = [
            'git', 'clone', 
            '--depth', '1',
            '--branch', deployment.branch,
            deployment.get_clone_url(),
            repo_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f'Error clonando repositorio: {result.stderr}')
        
        self._log(deployment, 'info', 'Repositorio clonado exitosamente')
        return repo_path
    
    async def _build_docker_image(self, deployment: Deployment, repo_path: str) -> str:
        """Construir imagen Docker"""
        
        image_name = f"dess-deploy-{deployment.id}"
        deployment.image_name = image_name
        deployment.save()
        
        self._log(deployment, 'info', f'Construyendo imagen Docker: {image_name}')
        
        try:
            # Verificar conexión Docker antes de construir
            self.docker_client.ping()
            
            # Construir imagen
            image, build_logs = self.docker_client.images.build(
                path=repo_path,
                tag=image_name,
                rm=True,
                forcerm=True
            )
            
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
            error_msg = f"Error construyendo imagen: {str(e)}"
            deployment.build_logs = error_msg
            deployment.save()
            raise Exception(error_msg)
        except Exception as e:
            if "http+docker" in str(e):
                error_msg = "Docker daemon no está disponible. Inicia Docker Desktop y asegúrate de que esté ejecutándose correctamente."
            else:
                error_msg = f"Error inesperado construyendo imagen: {str(e)}"
            deployment.build_logs = error_msg
            deployment.save()
            raise Exception(error_msg)
    
    async def _deploy_container(self, deployment: Deployment, image_name: str) -> str:
        """Desplegar contenedor Docker"""
        
        # Obtener configuración del proyecto
        config = deployment.get_project_config()
        port = deployment.port or config.get('port', 8000)
        
        # Asignar puerto disponible
        available_port = self._get_available_port()
        deployment.port = available_port
        deployment.deploy_url = f"http://localhost:{available_port}"
        deployment.save()
        
        self._log(deployment, 'info', f'Desplegando en puerto {available_port}')
        
        try:
            # Verificar conexión Docker antes de desplegar
            self.docker_client.ping()
            
            # Crear y ejecutar contenedor
            container = self.docker_client.containers.run(
                image_name,
                detach=True,
                ports={f'{port}/tcp': available_port},
                environment=deployment.environment_vars,
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
    
    async def _verify_deployment(self, deployment: Deployment) -> bool:
        """Verificar que el despliegue esté funcionando"""
        
        if not deployment.deploy_url:
            return False
        
        try:
            # Esperar un momento para que el servicio inicie
            import time
            time.sleep(5)
            
            response = requests.get(deployment.deploy_url, timeout=10)
            
            if response.status_code == 200:
                self._log(deployment, 'success', 'Verificación de salud exitosa')
                return True
            else:
                self._log(deployment, 'warning', f'Respuesta inesperada: {response.status_code}')
                return False
                
        except requests.RequestException as e:
            self._log(deployment, 'warning', f'Error en verificación: {str(e)}')
            return False
    
    def _get_available_port(self) -> int:
        """Obtener un puerto disponible para el despliegue"""
        import socket
        
        # Rango de puertos para despliegues
        start_port = 8100
        max_port = 8200
        
        for port in range(start_port, max_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    continue
        
        raise Exception("No hay puertos disponibles para el despliegue")
    
    async def _log(self, deployment: Deployment, level: str, message: str, details: Dict = None):
        """Agregar log al despliegue"""
        
        await sync_to_async(DeploymentLog.objects.create)(
            deployment=deployment,
            level=level,
            message=message,
            details=details or {}
        )
        
        logger.info(f"[{deployment.name}] {message}")
    
    async def _save_deployment(self, deployment: Deployment):
        """Guardar deployment de forma asíncrona"""
        await sync_to_async(deployment.save)()
    
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
                
                self._log(deployment, 'info', 'Despliegue detenido')
                return True
                
            except docker.errors.NotFound:
                self._log(deployment, 'warning', 'Contenedor no encontrado')
                deployment.status = DeploymentStatus.STOPPED
                deployment.save()
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
    
    async def _deploy_project_simulation(self, deployment: Deployment) -> bool:
        """Simular despliegue cuando Docker no está disponible"""
        
        try:
            await self._log(deployment, 'info', '🎭 Iniciando despliegue en modo simulación')
            
            # 1. Simular clonación
            deployment.status = DeploymentStatus.CLONING
            await self._save_deployment(deployment)
            await self._log(deployment, 'info', f'📥 Simulando clonación de {deployment.github_url}')
            await asyncio.sleep(1)  # Simular tiempo de clonación
            
            # 2. Simular análisis
            deployment.status = DeploymentStatus.ANALYZING  
            await self._save_deployment(deployment)
            await self._log(deployment, 'info', '🔍 Simulando análisis de proyecto')
            await asyncio.sleep(0.5)
            
            # Detectar tipo de proyecto basado en la URL (simulado)
            if not deployment.project_type:
                if 'react' in deployment.github_url.lower():
                    deployment.project_type = ProjectType.REACT
                elif 'django' in deployment.github_url.lower():
                    deployment.project_type = ProjectType.DJANGO
                elif 'node' in deployment.github_url.lower():
                    deployment.project_type = ProjectType.NODE
                else:
                    deployment.project_type = ProjectType.STATIC
                await self._save_deployment(deployment)
            
            await self._log(deployment, 'info', f'📋 Tipo de proyecto detectado: {deployment.get_project_type_display()}')
            
            # 3. Simular construcción
            deployment.status = DeploymentStatus.BUILDING
            await self._save_deployment(deployment)
            await self._log(deployment, 'info', '🔨 Simulando construcción de imagen Docker')
            await asyncio.sleep(2)  # Simular tiempo de build
            
            deployment.image_name = f"dess-simulation-{deployment.id}"
            await self._save_deployment(deployment)
            
            # 4. Simular despliegue
            deployment.status = DeploymentStatus.DEPLOYING
            await self._save_deployment(deployment)
            await self._log(deployment, 'info', '🚀 Simulando despliegue de contenedor')
            await asyncio.sleep(1)
            
            # Asignar puerto simulado
            if not deployment.port:
                deployment.port = self._get_available_port_simulation()
            
            # Generar URL de acceso
            deployment.deploy_url = f"http://localhost:{deployment.port}"
            deployment.container_id = f"simulation-container-{deployment.id}"
            await self._save_deployment(deployment)
            
            # 5. Verificar despliegue (simulado)
            await self._log(deployment, 'info', '✅ Simulando verificación de despliegue')
            await asyncio.sleep(0.5)
            
            # Marcar como exitoso
            deployment.status = DeploymentStatus.RUNNING
            deployment.last_deployed = timezone.now()
            await self._save_deployment(deployment)
            
            # Log de éxito con información de acceso
            await self._log(deployment, 'success', f'🎉 Despliegue simulado completado exitosamente!')
            await self._log(deployment, 'info', f'🌐 URL de acceso: {deployment.deploy_url}')
            await self._log(deployment, 'info', f'🔗 Puerto asignado: {deployment.port}')
            await self._log(deployment, 'info', f'📦 Tipo: {deployment.get_project_type_display()}')
            
            # Actualizar logs de despliegue
            deployment.deploy_logs += f'\n\n=== DESPLIEGUE SIMULADO COMPLETADO ===\n'
            deployment.deploy_logs += f'✅ Estado: {deployment.get_status_display()}\n'
            deployment.deploy_logs += f'🌐 URL: {deployment.deploy_url}\n'
            deployment.deploy_logs += f'🔗 Puerto: {deployment.port}\n'
            deployment.deploy_logs += f'📦 Tipo: {deployment.get_project_type_display()}\n'
            deployment.deploy_logs += f'🕒 Desplegado: {deployment.last_deployed.strftime("%Y-%m-%d %H:%M:%S")}\n'
            await self._save_deployment(deployment)
            
            return True
            
        except Exception as e:
            await self._log(deployment, 'error', f'❌ Error en despliegue simulado: {str(e)}')
            deployment.status = DeploymentStatus.FAILED
            await self._save_deployment(deployment)
            return False
    
    def _get_available_port_simulation(self) -> int:
        """Obtener un puerto disponible para simulación"""
        # Generar puerto simulado entre 3000-9000 
        base_ports = [3000, 3001, 4000, 5000, 8000, 8080, 8081, 9000]
        return random.choice(base_ports)