# Genera .env.docker con contraseñas y claves ALEATORIAS (solo si no existe). No imprime los secretos.
# Lo usa iniciar-docker.bat; también puede ejecutarse a mano:  powershell -File scripts\generar_env_docker.ps1
$destino = Join-Path (Split-Path $PSScriptRoot -Parent) ".env.docker"
if (Test-Path $destino) { Write-Host ".env.docker ya existe: se conserva."; exit 0 }

function Aleatorio([int]$n) {
    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count $n | ForEach-Object { [char]$_ })
}
$bytes = New-Object byte[] 48
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$secreto = [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_').TrimEnd('=')

@"
# Configuración para docker compose (generada automáticamente; NO subir a Git ni compartir).
POSTGRES_PASSWORD=$(Aleatorio 28)
APP_DB_PASSWORD=$(Aleatorio 28)
SECRET_KEY=$secreto
INTEGRATION_API_KEY=$(Aleatorio 32)
ADMIN_EMAIL=admin@salesx.local
ADMIN_PASSWORD=$(Aleatorio 16)a9
"@ | Set-Content -Path $destino -Encoding ascii

Write-Host ".env.docker creado con secretos aleatorios."
