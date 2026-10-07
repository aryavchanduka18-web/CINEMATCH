# Start or stop the PostgreSQL container.  Usage: scripts\db.ps1 [start|stop|status|logs]
param([ValidateSet("start", "stop", "status", "logs")][string]$Action = "start")
. "$PSScriptRoot\_common.ps1"
Push-Location $Root
try {
    switch ($Action) {
        "start" {
            docker compose up -d --wait db
            if ($LASTEXITCODE -ne 0) { throw "Could not start the database. Is Docker Desktop running?" }
            Write-Host "PostgreSQL is running on localhost:$(Get-EnvValue 'POSTGRES_PORT' '5432')"
        }
        "stop"   { docker compose stop db }
        "status" { docker compose ps db }
        "logs"   { docker compose logs --tail 50 db }
    }
} finally { Pop-Location }