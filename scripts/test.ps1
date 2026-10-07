# Run every test suite: engine (pytest), api (pytest, needs the database running), web (vitest).
. "$PSScriptRoot\_common.ps1"
$failed = @()

Write-Host "`n== engine tests ==" -ForegroundColor Cyan
Push-Location (Join-Path $Root "engine"); & $Python -m pytest -q; if ($LASTEXITCODE -ne 0) { $failed += "engine" }; Pop-Location

Write-Host "`n== pipeline tests ==" -ForegroundColor Cyan
Push-Location (Join-Path $Root "pipeline"); & $Python -m pytest -q; if ($LASTEXITCODE -ne 0) { $failed += "pipeline" }; Pop-Location

Write-Host "`n== api tests ==" -ForegroundColor Cyan
Push-Location (Join-Path $Root "api"); & $Python -m pytest -q; if ($LASTEXITCODE -ne 0) { $failed += "api" }; Pop-Location

Write-Host "`n== web tests ==" -ForegroundColor Cyan
Push-Location (Join-Path $Root "web"); npm test --silent; if ($LASTEXITCODE -ne 0) { $failed += "web" }; Pop-Location

if ($failed.Count -gt 0) { Write-Host "`nFAILED: $($failed -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "`nAll tests passed." -ForegroundColor Green