# Apply all database migrations (alembic upgrade head).
. "$PSScriptRoot\_common.ps1"
Push-Location (Join-Path $Root "api")
try {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Migration failed." }
} finally { Pop-Location }