# Shared helpers for the CineMatch scripts. Dot-source this file: . "$PSScriptRoot\_common.ps1"
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    throw "Missing .env in $Root. Copy .env.example to .env and fill in the values."
}

function Get-EnvValue([string]$Name, [string]$Default = "") {
    $line = Get-Content (Join-Path $Root ".env") | Where-Object { $_ -match "^\s*$Name=" } | Select-Object -First 1
    if ($line) { return ($line -split "=", 2)[1].Trim() }
    return $Default
}