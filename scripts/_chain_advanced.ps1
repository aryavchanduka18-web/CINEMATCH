$ErrorActionPreference = 'Continue'
Set-Location 'C:\PROJECTS\RS PROJECT\cinematch'
$env:OPENBLAS_NUM_THREADS = '1'
while (-not (Test-Path data\logs\chain2_done.txt)) { Start-Sleep 20 }
.\.venv\Scripts\python.exe -u -m pipeline.13_shilling *> data\logs\step13.log
.\.venv\Scripts\python.exe -u -m pipeline.15_ncf *> data\logs\step15.log
'advanced finished' | Out-File data\logs\chain3_done.txt