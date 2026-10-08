# CineMatch in one container: the built website plus the FastAPI server that also serves it.
# Model artifacts and the film catalog are NOT in the image; they live in the hosted database
# (see docs/deploy.md and scripts/deploy_data.py).

# 1) Build the website
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2) Python server
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    # one BLAS thread each: lower memory, and the free plan has a fraction of one CPU anyway
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    # fewer malloc arenas: each request thread would otherwise keep its own heap
    MALLOC_ARENA_MAX=2 \
    PRELOAD_ENGINE=true
WORKDIR /app
COPY engine/ engine/
RUN pip install ./engine
COPY api/ api/
RUN pip install -e ./api
COPY deploy/start.sh deploy/start.sh
COPY --from=web /web/dist web/dist
RUN mkdir -p artifacts && useradd --create-home cinematch && chown -R cinematch /app/artifacts
USER cinematch
EXPOSE 8000
CMD ["sh", "deploy/start.sh"]
