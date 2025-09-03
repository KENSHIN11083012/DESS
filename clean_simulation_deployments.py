#!/usr/bin/env python3
"""
Script para limpiar deployments de simulación - DESS
Limpia deployments antiguos que fueron creados en modo simulación
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructure.database.models_package.deployment import Deployment, DeploymentStatus

def main():
    """Limpiar deployments de simulación"""
    print("Limpiando deployments de simulacion...")
    
    # Encontrar todos los deployments de simulación
    simulation_deployments = Deployment.objects.filter(
        container_id__startswith='simulation-container-'
    )
    
    count = simulation_deployments.count()
    print(f"Encontrados {count} deployments de simulacion")
    
    if count == 0:
        print("No hay deployments de simulacion para limpiar")
        return
    
    # Mostrar detalles de los deployments
    for deployment in simulation_deployments:
        print(f"Deployment: {deployment.name} (ID: {deployment.id})")
        print(f"   Estado: {deployment.status}")
        print(f"   Container ID: {deployment.container_id}")
        print(f"   Imagen: {deployment.image_name}")
        print(f"   URL: {deployment.deploy_url}")
        print()
    
    # Confirmar acción
    confirm = input(f"Deseas limpiar estos {count} deployments? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Operacion cancelada")
        return
    
    # Limpiar deployments
    updated = 0
    for deployment in simulation_deployments:
        # Actualizar estado y limpiar campos
        deployment.status = DeploymentStatus.FAILED
        deployment.container_id = ""  # Cadena vacía
        deployment.image_name = ""  # Cadena vacía
        deployment.deploy_url = ""  # Cadena vacía
        deployment.port = None
        deployment.save()
        
        print(f"Limpiado: {deployment.name}")
        updated += 1
    
    print(f"Limpieza completada: {updated} deployments actualizados")
    print("Estado cambiado a 'FAILED'")
    print("Campos container_id, image_name, deploy_url y port limpiados")

if __name__ == "__main__":
    main()