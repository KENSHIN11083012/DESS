# Script PowerShell para iniciar DESS
# Uso: .\start_dess.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    DESS - Iniciando Servidor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Verificar que estemos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: No se encontró manage.py" -ForegroundColor Red
    Write-Host "Asegúrate de estar en el directorio del proyecto DESS" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar entorno virtual
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ Error: No se encontró el entorno virtual" -ForegroundColor Red
    Write-Host "Por favor ejecuta: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Activar entorno virtual
Write-Host "🔄 Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Verificar configuración Django
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" "manage.py" "check"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Hay problemas con la configuración de Django" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para diagnosticar ejecuta: python diagnose_dess.py" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "✅ Sistema DESS listo" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs Disponibles:" -ForegroundColor Cyan
Write-Host "   Login: http://127.0.0.1:8000/login/" -ForegroundColor White
Write-Host "   Admin: http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "   API:   http://127.0.0.1:8000/api/docs/" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Credenciales de Admin:" -ForegroundColor Cyan
Write-Host "   Usuario: admin" -ForegroundColor White
Write-Host "   Contraseña: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Iniciar servidor Django
& ".\venv\Scripts\python.exe" "manage.py" "runserver" "127.0.0.1:8000"
