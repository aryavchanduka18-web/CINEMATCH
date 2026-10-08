$ErrorActionPreference = 'Continue'
Set-Location 'C:\PROJECTS\RS PROJECT\cinematch'
$env:OPENBLAS_NUM_THREADS = '1'
Wait-Process -Id 51368 -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -u -c "import importlib; m=importlib.import_module('pipeline.09_train_models'); ctx=m.Ctx(); print('popularity rows', m.write_popularity_to_db(m.popularity_scores(ctx, 0)))" *> data\logs\popularity_display.log
.\.venv\Scripts\python.exe -u -m pipeline.10_tune_hybrid --refit *> data\logs\step10.log
.\.venv\Scripts\python.exe -u -m pipeline.11_evaluate *> data\logs\step11.log
.\.venv\Scripts\python.exe -u -m pipeline.report_validation *> data\logs\report.log
'chain finished' | Out-File data\logs\chain_done.txt