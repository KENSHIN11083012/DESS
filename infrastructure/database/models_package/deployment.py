"""
Modelos para gestión de despliegues automatizados - DESS
"""
from django.db import models
from django.utils import timezone
import uuid
import json


class ProjectType(models.TextChoices):
    """Tipos de proyecto soportados para despliegue"""
    DJANGO = 'django', 'Django'
    REACT = 'react', 'React'
    NODE = 'node', 'Node.js'
    NEXTJS = 'nextjs', 'Next.js'
    FLASK = 'flask', 'Flask'
    FASTAPI = 'fastapi', 'FastAPI'
    STATIC = 'static', 'Static Site'
    DOCKER = 'docker', 'Docker'


class DeploymentStatus(models.TextChoices):
    """Estados de despliegue"""
    PENDING = 'pending', 'Pendiente'
    CLONING = 'cloning', 'Clonando repositorio'
    ANALYZING = 'analyzing', 'Analizando proyecto'
    BUILDING = 'building', 'Construyendo'
    DEPLOYING = 'deploying', 'Desplegando'
    RUNNING = 'running', 'En ejecución'
    FAILED = 'failed', 'Falló'
    STOPPED = 'stopped', 'Detenido'


class Deployment(models.Model):
    """Modelo para gestionar despliegues de proyectos"""
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Nombre del despliegue")
    description = models.TextField(blank=True, help_text="Descripción del proyecto")
    
    # Repositorio
    github_url = models.URLField(help_text="URL del repositorio GitHub")
    branch = models.CharField(max_length=100, default='main', help_text="Rama a desplegar")
    
    # Tipo y configuración
    project_type = models.CharField(
        max_length=20,
        choices=ProjectType.choices,
        blank=True,
        help_text="Tipo de proyecto (auto-detectado)"
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=DeploymentStatus.choices,
        default=DeploymentStatus.PENDING
    )
    
    # URLs y puertos
    deploy_url = models.URLField(blank=True, help_text="URL donde está desplegado")
    port = models.IntegerField(blank=True, null=True, help_text="Puerto asignado")
    
    # Configuración Docker
    dockerfile_path = models.CharField(
        max_length=255,
        default="Dockerfile",
        help_text="Ruta al Dockerfile"
    )
    build_command = models.TextField(blank=True, help_text="Comando de construcción personalizado")
    start_command = models.TextField(blank=True, help_text="Comando de inicio personalizado")
    
    # Variables de entorno
    environment_vars = models.JSONField(
        default=dict,
        help_text="Variables de entorno para el despliegue"
    )
    
    # Información del contenedor
    container_id = models.CharField(max_length=255, blank=True)
    image_name = models.CharField(max_length=255, blank=True)
    
    # Logs
    build_logs = models.TextField(blank=True)
    deploy_logs = models.TextField(blank=True)
    error_logs = models.TextField(blank=True)
    
    # Metadatos
    created_by = models.ForeignKey('database.DESSUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_deployed = models.DateTimeField(blank=True, null=True)
    
    # Webhook
    webhook_secret = models.CharField(max_length=255, blank=True, help_text="Secret para webhook")
    auto_deploy = models.BooleanField(default=False, help_text="Auto-desplegar en push")
    
    class Meta:
        db_table = 'dess_deployments'
        ordering = ['-created_at']
        verbose_name = 'Despliegue'
        verbose_name_plural = 'Despliegues'
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_repo_name(self):
        """Extraer nombre del repositorio de la URL"""
        if self.github_url:
            return self.github_url.rstrip('/').split('/')[-1].replace('.git', '')
        return ''
    
    def get_clone_url(self):
        """URL para clonar el repositorio"""
        return f"{self.github_url}.git"
    
    def add_log(self, log_type, message):
        """Agregar mensaje al log correspondiente"""
        current_logs = getattr(self, f"{log_type}_logs", "")
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        new_log = f"[{timestamp}] {message}\n"
        setattr(self, f"{log_type}_logs", current_logs + new_log)
        self.save(update_fields=[f"{log_type}_logs"])
    
    def get_project_config(self):
        """Obtener configuración específica del tipo de proyecto"""
        configs = {
            ProjectType.DJANGO: {
                'port': 8000,
                'dockerfile_template': 'django.dockerfile',
                'build_command': 'pip install -r requirements.txt && python manage.py collectstatic --noinput',
                'start_command': 'python manage.py runserver 0.0.0.0:8000',
                'health_check': '/health/',
            },
            ProjectType.REACT: {
                'port': 3000,
                'dockerfile_template': 'react.dockerfile',
                'build_command': 'npm install && npm run build',
                'start_command': 'npm start',
                'health_check': '/',
            },
            ProjectType.NODE: {
                'port': 3000,
                'dockerfile_template': 'node.dockerfile',
                'build_command': 'npm install',
                'start_command': 'npm start',
                'health_check': '/',
            },
            ProjectType.NEXTJS: {
                'port': 3000,
                'dockerfile_template': 'nextjs.dockerfile',
                'build_command': 'npm install && npm run build',
                'start_command': 'npm start',
                'health_check': '/',
            },
        }
        return configs.get(self.project_type, {})


class DeploymentLog(models.Model):
    """Logs detallados de despliegues"""
    
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(
        max_length=10,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('success', 'Success'),
        ]
    )
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'dess_deployment_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.deployment.name} - {self.level}: {self.message[:50]}"


class WebhookEvent(models.Model):
    """Registro de eventos de webhook"""
    
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='webhook_events')
    event_type = models.CharField(max_length=50)  # push, pull_request, etc.
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    triggered_deployment = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dess_webhook_events'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.deployment.name} - {self.event_type} - {self.created_at}"