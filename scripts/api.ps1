# Run the FastAPI server with auto-reload on http://127.0.0.1:<API_PORT>
. "$PSScriptRoot\_common.ps1"
$port = Get-EnvValue "API_PORT" "8010"
Push-Location (Join-Path $Root "api")
try {
    & $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
} finally { Pop-Location }