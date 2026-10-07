# Run the offline data pipeline.  Usage: scripts\data.ps1 [-From N] [-Only N]
param([int]$From = 1, [int]$Only = 0)
. "$PSScriptRoot\_common.ps1"
Push-Location $Root
try {
    $pipelineArgs = @("-m", "pipeline.run_all")
    if ($Only -gt 0) { $pipelineArgs += @("--only", $Only) } else { $pipelineArgs += @("--from", $From) }
    & $Python @pipelineArgs
    if ($LASTEXITCODE -ne 0) { throw "Pipeline failed." }
} finally { Pop-Location }