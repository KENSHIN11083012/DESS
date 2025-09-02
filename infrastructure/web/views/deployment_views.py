"""
Vistas para Gestión de Despliegues - DESS
"""
import json
import asyncio
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse

from infrastructure.database.models_package.deployment import (
    Deployment, DeploymentStatus, ProjectType, WebhookEvent
)
from application.services.deployment_service import DeploymentService
from core.entities.user import User

import logging
logger = logging.getLogger(__name__)


@login_required
def deployments_list_view(request):
    """Lista de despliegues"""
    
    # Solo super admins pueden ver despliegues
    if request.user.role != 'super_admin':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('dashboard')
    
    deployments = Deployment.objects.select_related('created_by').all()
    
    # Filtros
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    search = request.GET.get('search')
    
    if status_filter and status_filter != 'all':
        deployments = deployments.filter(status=status_filter)
    
    if type_filter and type_filter != 'all':
        deployments = deployments.filter(project_type=type_filter)
    
    if search:
        deployments = deployments.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(github_url__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(deployments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'deployments': page_obj,
        'status_choices': DeploymentStatus.choices,
        'type_choices': ProjectType.choices,
        'current_status': status_filter,
        'current_type': type_filter,
        'current_search': search,
    }
    
    return render(request, 'deployment/deployments_list.html', context)


@login_required
def deployment_detail_view(request, deployment_id):
    """Detalle de un despliegue"""
    
    if request.user.role != 'super_admin':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('dashboard')
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    # Obtener logs recientes
    recent_logs = deployment.logs.all()[:50]
    
    context = {
        'deployment': deployment,
        'recent_logs': recent_logs,
        'can_start': deployment.status in [DeploymentStatus.STOPPED, DeploymentStatus.FAILED],
        'can_stop': deployment.status == DeploymentStatus.RUNNING,
        'can_restart': deployment.status == DeploymentStatus.RUNNING,
    }
    
    return render(request, 'deployment/deployment_detail.html', context)


@login_required
def create_deployment_view(request):
    """Crear nuevo despliegue"""
    
    logger.info(f"create_deployment_view called - Method: {request.method}, User: {request.user.username}")
    
    if request.user.role != 'super_admin':
        logger.warning(f"User {request.user.username} with role {request.user.role} tried to access deployment creation")
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('dashboard')
    
    if request.method == 'POST':
        logger.info("Processing POST request for deployment creation")
        logger.info(f"POST data keys: {list(request.POST.keys())}")
        
        try:
            # Obtener datos del formulario
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            github_url = request.POST.get('github_url')
            branch = request.POST.get('branch', 'main')
            auto_deploy = request.POST.get('auto_deploy') == 'on'
            
            logger.info(f"Form data - Name: {name}, GitHub URL: {github_url}, Branch: {branch}, Auto-deploy: {auto_deploy}")
            
            # Variables de entorno
            env_vars = {}
            env_keys = request.POST.getlist('env_key[]')
            env_values = request.POST.getlist('env_value[]')
            
            logger.info(f"Environment variables - Keys: {env_keys}, Values: {env_values}")
            
            for key, value in zip(env_keys, env_values):
                if key and value:
                    env_vars[key] = value
            
            logger.info(f"Processed environment variables: {env_vars}")
            
            # Validaciones básicas
            if not all([name, github_url]):
                logger.error(f"Validation failed - Name: {name}, GitHub URL: {github_url}")
                messages.error(request, 'Nombre y URL de GitHub son obligatorios')
                return render(request, 'deployment/create_deployment.html')
            
            logger.info("Validation passed, creating deployment service")
            
            # Crear el despliegue
            deployment_service = DeploymentService()
            logger.info("DeploymentService instantiated, calling create_deployment")
            
            deployment = deployment_service.create_deployment(
                github_url=github_url,
                name=name,
                created_by=request.user,
                description=description,
                branch=branch,
                auto_deploy=auto_deploy,
                environment_vars=env_vars
            )
            
            logger.info(f"Deployment created successfully with ID: {deployment.id}")
            messages.success(request, f'Despliegue "{name}" creado exitosamente')
            
            logger.info(f"Redirecting to deployment_detail with ID: {deployment.id}")
            return redirect('deployment_detail', deployment_id=deployment.id)
            
        except Exception as e:
            logger.error(f"Error creando despliegue: {str(e)}", exc_info=True)
            messages.error(request, f'Error creando despliegue: {str(e)}')
    else:
        logger.info("GET request - showing create deployment form")
    
    return render(request, 'deployment/create_deployment.html')


@login_required
@require_http_methods(["POST"])
def deploy_project_action(request, deployment_id):
    """Ejecutar despliegue de un proyecto"""
    
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    try:
        deployment_service = DeploymentService()
        
        # Ejecutar despliegue de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            deployment_service.deploy_project(deployment)
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Despliegue iniciado exitosamente',
                'deploy_url': deployment.deploy_url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en el despliegue. Revisa los logs.'
            })
            
    except Exception as e:
        logger.error(f"Error en despliegue {deployment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error ejecutando despliegue: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def stop_deployment_action(request, deployment_id):
    """Detener un despliegue"""
    
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    try:
        deployment_service = DeploymentService()
        success = deployment_service.stop_deployment(deployment)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Despliegue detenido exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error deteniendo despliegue'
            })
            
    except Exception as e:
        logger.error(f"Error deteniendo despliegue {deployment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def restart_deployment_action(request, deployment_id):
    """Reiniciar un despliegue"""
    
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    try:
        deployment_service = DeploymentService()
        success = deployment_service.restart_deployment(deployment)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Despliegue reiniciado exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error reiniciando despliegue'
            })
            
    except Exception as e:
        logger.error(f"Error reiniciando despliegue {deployment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
def deployment_logs_view(request, deployment_id):
    """Obtener logs de un despliegue (AJAX)"""
    
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    # Tipo de log solicitado
    log_type = request.GET.get('type', 'all')
    
    logs = deployment.logs.all()
    
    if log_type != 'all':
        logs = logs.filter(level=log_type)
    
    logs_data = []
    for log in logs[:100]:  # Últimos 100 logs
        logs_data.append({
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': log.level,
            'message': log.message,
            'details': log.details
        })
    
    return JsonResponse({
        'success': True,
        'logs': logs_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def github_webhook_view(request, deployment_id):
    """Endpoint para webhook de GitHub"""
    
    deployment = get_object_or_404(Deployment, id=deployment_id)
    
    try:
        # Verificar que el despliegue tenga auto-deploy habilitado
        if not deployment.auto_deploy:
            return HttpResponse("Auto-deploy not enabled", status=400)
        
        # Obtener payload del webhook
        payload = json.loads(request.body)
        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        
        # Crear registro del evento
        webhook_event = WebhookEvent.objects.create(
            deployment=deployment,
            event_type=event_type,
            payload=payload
        )
        
        # Solo procesar eventos de push a la rama correcta
        if event_type == 'push':
            branch_ref = payload.get('ref', '')
            target_branch = f"refs/heads/{deployment.branch}"
            
            if branch_ref == target_branch:
                webhook_event.triggered_deployment = True
                webhook_event.save()
                
                # Ejecutar despliegue automático
                try:
                    deployment_service = DeploymentService()
                    
                    # Ejecutar en thread separado para no bloquear webhook
                    import threading
                    
                    def deploy_async():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            deployment_service.deploy_project(deployment)
                        )
                    
                    thread = threading.Thread(target=deploy_async)
                    thread.start()
                    
                    logger.info(f"Auto-deploy iniciado para {deployment.name}")
                    
                except Exception as e:
                    logger.error(f"Error en auto-deploy: {str(e)}")
        
        webhook_event.processed = True
        webhook_event.save()
        
        return HttpResponse("Webhook processed", status=200)
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return HttpResponse("Error processing webhook", status=500)


@login_required
def detect_project_type_ajax(request):
    """Detectar tipo de proyecto desde URL de GitHub (AJAX)"""
    
    if request.user.role != 'super_admin':
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    github_url = request.GET.get('url')
    if not github_url:
        return JsonResponse({'success': False, 'message': 'URL requerida'})
    
    try:
        from application.services.deployment_service import ProjectDetector
        import tempfile
        import subprocess
        import shutil
        
        # Clonar temporalmente para detectar tipo
        temp_dir = tempfile.mkdtemp()
        
        try:
            cmd = ['git', 'clone', '--depth', '1', f"{github_url}.git", temp_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                project_type = ProjectDetector.detect_project_type(temp_dir)
                
                return JsonResponse({
                    'success': True,
                    'project_type': project_type,
                    'project_type_display': ProjectType(project_type).label
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No se pudo acceder al repositorio'
                })
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        logger.error(f"Error detectando tipo de proyecto: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })