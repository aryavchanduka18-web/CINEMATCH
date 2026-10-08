$ErrorActionPreference = 'Continue'
Set-Location 'C:\PROJECTS\RS PROJECT\cinematch'
$env:OPENBLAS_NUM_THREADS = '1'
.\.venv\Scripts\python.exe -u -m pipeline.10_tune_hybrid *> data\logs\step10.log
.\.venv\Scripts\python.exe -u -m pipeline.11_evaluate *> data\logs\step11.log
.\.venv\Scripts\python.exe -u -m pipeline.report_validation *> data\logs\report.log
'chain finished' | Out-File data\logs\chain2_done.txt