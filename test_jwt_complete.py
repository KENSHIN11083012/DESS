#!/usr/bin/env python3
"""
Script completo para probar JWT en DESS
Ejecutar: python test_jwt_complete.py
"""

import requests
import json
import sys

# Configuración
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"  # Cambia por tu usuario
PASSWORD = "admin"  # Cambia por tu contraseña

def print_separator(title):
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def test_jwt_endpoints():
    """Prueba completa de JWT"""
    
    print_separator("🔍 VERIFICACIÓN COMPLETA DE JWT - DESS")
    
    # 1. Verificar que los endpoints existen
    print("\n1️⃣ Verificando endpoints JWT...")
    
    jwt_urls = [
        f"{BASE_URL}/auth/login/",      # Token obtain
        f"{BASE_URL}/auth/refresh/",    # Token refresh  
        f"{BASE_URL}/auth/verify/",     # Token verify
    ]
    
    for url in jwt_urls:
        try:
            response = requests.post(url, json={})
            print(f"   ✅ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {url} - Error: {e}")
    
    # 2. Obtener token JWT
    print_separator("🔑 OBTENIENDO TOKEN JWT")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
            if access_token:
                print("✅ JWT ACCESS TOKEN OBTENIDO CORRECTAMENTE")
                print(f"   Access Token: {access_token[:50]}...")
                print(f"   Refresh Token: {refresh_token[:50]}..." if refresh_token else "   No refresh token")
                
                # 3. Verificar token
                print_separator("🔍 VERIFICANDO TOKEN")
                
                verify_response = requests.post(
                    f"{BASE_URL}/auth/verify/",
                    json={"token": access_token}
                )
                
                print(f"Verify Status: {verify_response.status_code}")
                if verify_response.status_code == 200:
                    print("✅ TOKEN VÁLIDO")
                else:
                    print("❌ TOKEN INVÁLIDO")
                    print(f"Response: {verify_response.text}")
                
                # 4. Probar endpoint protegido con JWT
                print_separator("🛡️ PROBANDO ENDPOINT PROTEGIDO")
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Probar API de perfil
                try:
                    profile_response = requests.get(
                        f"{BASE_URL}/api/user/profile/",
                        headers=headers
                    )
                    print(f"Profile API Status: {profile_response.status_code}")
                    
                    if profile_response.status_code == 200:
                        print("✅ ENDPOINT PROTEGIDO FUNCIONA CON JWT")
                        profile_data = profile_response.json()
                        print(f"   Usuario: {profile_data.get('username', 'N/A')}")
                        print(f"   Email: {profile_data.get('email', 'N/A')}")
                    else:
                        print("❌ ENDPOINT PROTEGIDO NO FUNCIONA")
                        print(f"Response: {profile_response.text}")
                        
                except Exception as e:
                    print(f"❌ Error al probar endpoint protegido: {e}")
                
                # 5. Probar refresh token
                if refresh_token:
                    print_separator("🔄 PROBANDO REFRESH TOKEN")
                    
                    refresh_response = requests.post(
                        f"{BASE_URL}/auth/refresh/",
                        json={"refresh": refresh_token}
                    )
                    
                    print(f"Refresh Status: {refresh_response.status_code}")
                    if refresh_response.status_code == 200:
                        new_access = refresh_response.json().get('access')
                        print("✅ REFRESH TOKEN FUNCIONA")
                        print(f"   Nuevo Access Token: {new_access[:50]}...")
                    else:
                        print("❌ REFRESH TOKEN NO FUNCIONA")
                        print(f"Response: {refresh_response.text}")
                
            else:
                print("❌ NO SE OBTUVO ACCESS TOKEN")
                print(f"Response completa: {response.text}")
        else:
            print(f"❌ ERROR AL HACER LOGIN")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    # 6. Verificar configuración JWT en settings
    print_separator("⚙️ VERIFICANDO CONFIGURACIÓN")
    
    print("Para verificar la configuración JWT, revisa:")
    print("   ✓ INSTALLED_APPS tiene 'rest_framework_simplejwt'")
    print("   ✓ REST_FRAMEWORK tiene JWTAuthentication")
    print("   ✓ SIMPLE_JWT settings están configurados")
    print("   ✓ URLs JWT están incluidas en config/urls.py")
    
    print_separator("📊 RESUMEN")
    print("✅ = Funcionando correctamente")
    print("❌ = Necesita revisión")
    print("\nSi ves ✅ en todos los puntos, JWT está funcionando perfectamente!")

if __name__ == "__main__":
    print("🚀 Iniciando prueba completa de JWT...")
    print(f"📡 Servidor: {BASE_URL}")
    print(f"👤 Usuario: {USERNAME}")
    print("\n⚠️  IMPORTANTE: Asegúrate de que el servidor esté corriendo y que tengas un usuario creado.")
    
    input("Presiona ENTER para continuar...")
    
    test_jwt_endpoints()
