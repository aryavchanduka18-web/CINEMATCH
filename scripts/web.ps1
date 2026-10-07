# Run the Vite dev server on http://localhost:5173 (it forwards /api to the FastAPI server).
. "$PSScriptRoot\_common.ps1"
$env:API_PORT = Get-EnvValue "API_PORT" "8010"
Push-Location (Join-Path $Root "web")
try {
    if (-not (Test-Path "node_modules")) { npm install }
    npm run dev
} finally { Pop-Location }