#!/bin/sh
# Container start: bring the database schema up to date, unpack the model bundle if one was
# uploaded, then serve the API and the website on $PORT (Render sets it; 8000 locally).
set -e
cd /app/api
alembic upgrade head
python -m app.services.artifact_store || echo "artifact bundle not unpacked yet; the site retries on use"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips='*'
