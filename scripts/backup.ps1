# Back up the LIVE database (Neon) to backups\flickraven-YYYY-MM-DD.dump on this laptop. Run it once a month.
#   scripts\backup.ps1                 back up (keeps the newest 6 files)
#   scripts\backup.ps1 -Keep 12        keep more
# Needs Docker Desktop running and NEON_DATABASE_URL in .env. Backups hold users' emails and ratings:
# keep them on this laptop, never in GitHub (backups\ is in .gitignore) or in chats.
# Restoring is in docs/deploy.md, "Back up and restore".
param([int]$Keep = 6)
. "$PSScriptRoot\_common.ps1"

$url = Get-EnvValue "NEON_DATABASE_URL"
if (-not $url) { throw "NEON_DATABASE_URL is missing from .env (the Neon connection URL of the live site)." }
$url = $url -replace "^postgresql\+psycopg://", "postgresql://"

$dir = Join-Path $Root "backups"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$name = "flickraven-$(Get-Date -Format 'yyyy-MM-dd').dump"

Write-Host "Backing up the live database to backups\$name (a minute or two)..."
$env:SOURCE = $url
try {
    docker run --rm -e SOURCE -v "${dir}:/out" postgres:17 sh -c "pg_dump --format=custom --no-owner --no-privileges -d `"`$SOURCE`" -f /out/$name"
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed. Is Docker Desktop running, and is NEON_DATABASE_URL right?" }
} finally { Remove-Item Env:SOURCE -ErrorAction SilentlyContinue }

$file = Get-Item (Join-Path $dir $name)
if ($file.Length -lt 1MB) { throw "The backup is suspiciously small ($($file.Length) bytes). Check it before trusting it." }
Write-Host ("Done: {0} ({1:N0} MB)" -f $file.Name, ($file.Length / 1MB)) -ForegroundColor Green

$old = Get-ChildItem $dir -Filter "flickraven-*.dump" | Sort-Object Name -Descending | Select-Object -Skip $Keep
foreach ($f in $old) { Remove-Item $f.FullName; Write-Host "Removed old backup $($f.Name)" }
