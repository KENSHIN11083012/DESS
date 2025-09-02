#!/usr/bin/env python
"""
Script para ejecutar un deployment específico
"""
import os
import sys
import django
import asyncio
from asgiref.sync import sync_to_async

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructure.database.models_package.deployment import Deployment, DeploymentStatus
from application.services.deployment_service import DeploymentService


async def execute_specific_deployment():
    """Ejecutar deployment específico por ID"""
    
    deployment_id = "bedf8325-3dc1-43e5-95ab-9ac598ac104c"
    
    print("🚀 Ejecutando deployment específico...")
    print(f"ID: {deployment_id}")
    
    try:
        # Buscar deployment
        deployment = await sync_to_async(Deployment.objects.get)(id=deployment_id)
        print(f"✅ Deployment encontrado: {deployment.name}")
        print(f"   Estado actual: {deployment.get_status_display()}")
        print(f"   Repositorio: {deployment.github_url}")
        print()
        
        # Ejecutar deployment
        deployment_service = DeploymentService()
        print("🔄 Iniciando proceso de deployment...")
        
        success = await deployment_service.deploy_project(deployment)
        
        # Refrescar desde DB
        await sync_to_async(deployment.refresh_from_db)()
        
        print()
        print("=" * 50)
        if success:
            print("🎉 ¡DEPLOYMENT COMPLETADO EXITOSAMENTE!")
            print(f"   Estado final: {deployment.get_status_display()}")
            if deployment.port:
                print(f"   Puerto asignado: {deployment.port}")
            if deployment.deploy_url:
                print(f"   URL de acceso: {deployment.deploy_url}")
        else:
            print("❌ DEPLOYMENT FALLÓ")
            print(f"   Estado final: {deployment.get_status_display()}")
        print("=" * 50)
        
    except Deployment.DoesNotExist:
        print("❌ Deployment no encontrado")
        print("   Verifica que el ID sea correcto")
    except Exception as e:
        print(f"❌ Error ejecutando deployment: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("EJECUTAR DEPLOYMENT ESPECÍFICO - DESS")
    print("=" * 60)
    
    asyncio.run(execute_specific_deployment())