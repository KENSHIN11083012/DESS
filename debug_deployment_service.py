#!/usr/bin/env python3
"""
Script standalone para debugging del DeploymentService - DESS
Permite probar y debuggear el servicio de despliegue sin Django
"""
import os
import sys
import django
import logging
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_deployment.log')
    ]
)

# Importar después de configurar Django
from application.services.deployment_service import DeploymentService, ProjectDetector
from infrastructure.database.models_package.deployment import Deployment
from core.entities.user import User


class DeploymentDebugger:
    """Clase para debugging del servicio de despliegue"""
    
    def __init__(self):
        self.service = DeploymentService()
        self.logger = logging.getLogger(__name__)
    
    def test_docker_connection(self):
        """Probar conexión con Docker"""
        print("\n" + "="*50)
        print("🐳 PRUEBA DE CONEXIÓN DOCKER")
        print("="*50)
        
        if self.service.is_docker_available():
            print("✅ Docker está disponible")
            
            # Probar comando básico
            success, output = self.service.run_docker_command(['version'])
            if success:
                print(f"✅ Docker version:\n{output[:300]}...")
            else:
                print(f"❌ Error ejecutando 'docker version': {output}")
        else:
            print("❌ Docker no está disponible")
    
    def test_project_detection(self, github_url: str):
        """Probar detección de tipo de proyecto"""
        print("\n" + "="*50)
        print("🔍 PRUEBA DE DETECCIÓN DE PROYECTO")
        print("="*50)
        print(f"URL: {github_url}")
        
        # Simular repositorio clonado con archivos comunes
        test_files = {
            'django': ['manage.py', 'requirements.txt', 'settings.py'],
            'react': ['package.json', 'src/App.js', 'public/index.html'],
            'node': ['package.json', 'server.js', 'index.js'],
            'flask': ['app.py', 'requirements.txt'],
            'fastapi': ['main.py', 'requirements.txt'],
            'static': ['index.html', 'style.css'],
            'docker': ['Dockerfile', 'docker-compose.yml']
        }
        
        for project_type, files in test_files.items():
            print(f"\n🔸 Simulando proyecto {project_type}:")
            print(f"   Archivos: {', '.join(files)}")
            # Aquí podrías crear un directorio temporal con estos archivos
            # y probar ProjectDetector.detect_project_type()
    
    def create_test_deployment(self, github_url: str = "https://github.com/CIM-DESS/Validador-PIR.git"):
        """Crear un despliegue de prueba"""
        print("\n" + "="*50)
        print("📦 CREAR DESPLIEGUE DE PRUEBA")
        print("="*50)
        print(f"URL: {github_url}")
        
        # Obtener o crear usuario de prueba
        try:
            user = User.objects.filter(role='super_admin').first()
            if not user:
                print("❌ No se encontró usuario super_admin")
                return None
                
            print(f"👤 Usuario: {user.username} ({user.role})")
            
            # Crear despliegue
            deployment = self.service.create_deployment(
                github_url=github_url,
                name="Test Validador PIR",
                created_by=user,
                description="Despliegue de prueba para debugging",
                branch="main",
                auto_deploy=False
            )
            
            print(f"✅ Despliegue creado con ID: {deployment.id}")
            print(f"   Estado: {deployment.status}")
            print(f"   Tipo: {deployment.project_type}")
            
            return deployment
            
        except Exception as e:
            print(f"❌ Error creando despliegue: {e}")
            return None
    
    def test_deployment_process(self, deployment_id: str = None):
        """Probar proceso completo de despliegue"""
        print("\n" + "="*50)
        print("🚀 PRUEBA DE PROCESO DE DESPLIEGUE")
        print("="*50)
        
        # Obtener o crear despliegue
        if deployment_id:
            try:
                deployment = Deployment.objects.get(id=deployment_id)
                print(f"📦 Usando despliegue existente: {deployment.name}")
            except Deployment.DoesNotExist:
                print(f"❌ Despliegue {deployment_id} no encontrado")
                return
        else:
            deployment = self.create_test_deployment()
            if not deployment:
                return
        
        print(f"🎯 Iniciando despliegue de: {deployment.name}")
        print(f"   URL: {deployment.github_url}")
        print(f"   Estado inicial: {deployment.status}")
        
        # Ejecutar despliegue
        try:
            success = self.service.deploy_project(deployment)
            
            # Refrescar desde BD
            deployment.refresh_from_db()
            
            print(f"\n🏁 Resultado del despliegue:")
            print(f"   ✅ Éxito: {success}")
            print(f"   📊 Estado final: {deployment.status}")
            print(f"   🌐 URL de acceso: {deployment.deploy_url}")
            print(f"   🔗 Puerto: {deployment.port}")
            print(f"   📦 Tipo detectado: {deployment.project_type}")
            print(f"   🐳 Container ID: {deployment.container_id}")
            print(f"   🏷️ Imagen: {deployment.image_name}")
            
            # Mostrar logs
            logs = deployment.logs.all()[:10]
            if logs:
                print(f"\n📋 Últimos logs:")
                for log in logs:
                    print(f"   [{log.level.upper()}] {log.message}")
            
        except Exception as e:
            print(f"❌ Error durante despliegue: {e}")
            self.logger.exception("Error completo:")
    
    def list_existing_deployments(self):
        """Listar despliegues existentes"""
        print("\n" + "="*50)
        print("📋 DESPLIEGUES EXISTENTES")
        print("="*50)
        
        deployments = Deployment.objects.all()
        
        if not deployments:
            print("📭 No hay despliegues")
            return
        
        for deployment in deployments:
            print(f"🔹 {deployment.name} (ID: {deployment.id})")
            print(f"   Estado: {deployment.status}")
            print(f"   URL: {deployment.github_url}")
            print(f"   Puerto: {deployment.port}")
            print(f"   Creado: {deployment.created_at}")
            print()
    
    def run_interactive_menu(self):
        """Menú interactivo para debugging"""
        while True:
            print("\n" + "="*50)
            print("🛠️  DEBUGGING DEPLOYMENT SERVICE")
            print("="*50)
            print("1. Probar conexión Docker")
            print("2. Crear despliegue de prueba")
            print("3. Ejecutar despliegue completo")
            print("4. Listar despliegues existentes")
            print("5. Probar con ID específico")
            print("6. Ver logs detallados")
            print("0. Salir")
            print("-" * 50)
            
            opcion = input("Selecciona una opción: ").strip()
            
            if opcion == "1":
                self.test_docker_connection()
            elif opcion == "2":
                url = input("URL del repositorio (Enter para usar Validador-PIR): ").strip()
                if not url:
                    url = "https://github.com/CIM-DESS/Validador-PIR.git"
                self.create_test_deployment(url)
            elif opcion == "3":
                self.test_deployment_process()
            elif opcion == "4":
                self.list_existing_deployments()
            elif opcion == "5":
                deployment_id = input("ID del despliegue: ").strip()
                if deployment_id:
                    self.test_deployment_process(deployment_id)
            elif opcion == "6":
                print("📄 Ver archivo: debug_deployment.log")
                if os.path.exists('debug_deployment.log'):
                    with open('debug_deployment.log', 'r') as f:
                        lines = f.readlines()[-20:]  # Últimas 20 líneas
                        print(''.join(lines))
            elif opcion == "0":
                print("👋 Saliendo...")
                break
            else:
                print("❌ Opción inválida")
            
            input("\nPresiona Enter para continuar...")


def main():
    """Función principal"""
    print("🚀 Iniciando Debugging del DeploymentService")
    print("📁 Directorio actual:", os.getcwd())
    print("🐍 Python version:", sys.version)
    
    try:
        debugger = DeploymentDebugger()
        
        # Verificar configuración inicial
        print("\n🔧 Verificando configuración...")
        debugger.test_docker_connection()
        
        # Ejecutar menú interactivo
        debugger.run_interactive_menu()
        
    except KeyboardInterrupt:
        print("\n👋 Interrumpido por usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        logging.exception("Error fatal en debugging:")


if __name__ == "__main__":
    main()