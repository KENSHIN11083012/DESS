# 🔍 COMANDOS PARA PROBAR JWT EN DESS
# Copia y pega estos comandos en otra terminal (PowerShell)

# 1. OBTENER TOKEN JWT (cambia username y password por los tuyos)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login/" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin"}'

# 2. VERIFICAR TOKEN (reemplaza YOUR_TOKEN con el token obtenido arriba)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/verify/" -Method POST -ContentType "application/json" -Body '{"token":"YOUR_TOKEN"}'

# 3. USAR TOKEN EN ENDPOINT PROTEGIDO (reemplaza YOUR_TOKEN)
$headers = @{ "Authorization" = "Bearer YOUR_TOKEN" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/profile/" -Method GET -Headers $headers

# 4. REFRESH TOKEN (reemplaza YOUR_REFRESH_TOKEN)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/refresh/" -Method POST -ContentType "application/json" -Body '{"refresh":"YOUR_REFRESH_TOKEN"}'

# 📋 EJEMPLO COMPLETO PASO A PASO:

# Paso 1: Obtener tokens
$loginResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login/" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin"}'
$accessToken = $loginResponse.access
$refreshToken = $loginResponse.refresh

Write-Host "Access Token: $accessToken"
Write-Host "Refresh Token: $refreshToken"

# Paso 2: Usar el token
$headers = @{ "Authorization" = "Bearer $accessToken" }
$profileResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/profile/" -Method GET -Headers $headers

Write-Host "Profile Response:"
$profileResponse

# 🎯 RESULTADOS ESPERADOS:
# ✅ Login debe devolver access y refresh tokens
# ✅ Verify debe devolver 200 para token válido  
# ✅ Profile debe devolver datos del usuario con token
# ✅ Refresh debe devolver nuevo access token
