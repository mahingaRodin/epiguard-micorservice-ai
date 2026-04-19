# ═══════════════════════════════════════════════════════════════════════════════
# epiguard-ai — Dockerfile
# Multi-stage build with 4 targets:
#   base     → shared Python + system deps (not used directly)
#   deps     → all pip dependencies installed
#   trainer  → model training + evaluation only (no API server)
#   runtime  → production FastAPI + gRPC server (smallest image)
#   jupyter  → dev/EDA environment with JupyterLab
#
# Build examples:
#   docker build --target runtime  -t epiguard-ai:latest .
#   docker build --target trainer  -t epiguard-ai-trainer:latest .
#   docker build --target jupyter  -t epiguard-ai-jupyter:latest .
# ═══════════════════════════════════════════════════════════════════════════════


# ─── Stage 1: base ────────────────────────────────────────────────────────────
# Shared OS-level deps + non-root user setup
FROM python:3.11-slim AS base

# Keeps Python from generating .pyc files and forces stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # pip tuning
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# System deps needed by grpcio, psycopg2, scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        curl \
        # Required by grpcio build
        libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Non-root user — never run ML services as root
RUN groupadd --gid 1001 epiguard \
    && useradd --uid 1001 --gid epiguard --shell /bin/bash --create-home epiguard

WORKDIR /app


# ─── Stage 2: deps ────────────────────────────────────────────────────────────
# Install all Python dependencies into a separate layer.
# This layer is cached as long as requirements.txt doesn't change.
FROM base AS deps

COPY requirements.txt .

# Install core runtime deps only (no jupyter/dev tools)
RUN pip install --no-cache-dir -r requirements.txt


# ─── Stage 3: proto-builder ───────────────────────────────────────────────────
# Generates triage_pb2.py and triage_pb2_grpc.py from triage.proto.
# Kept as a separate stage so proto regeneration doesn't bust the deps cache.
FROM deps AS proto-builder

COPY proto/triage.proto /proto/triage.proto

RUN python -m grpc_tools.protoc \
        -I /proto \
        --python_out=/app \
        --grpc_python_out=/app \
        /proto/triage.proto

# Verify generated files exist before proceeding
RUN test -f /app/triage_pb2.py && test -f /app/triage_pb2_grpc.py \
    && echo "Proto generation successful"


# ─── Stage 4: runtime ─────────────────────────────────────────────────────────
# Production image — FastAPI HTTP + gRPC server.
# Smallest possible image: no jupyter, no training scripts, no raw data.
FROM deps AS runtime

# Copy proto-generated files
COPY --from=proto-builder /app/triage_pb2.py .
COPY --from=proto-builder /app/triage_pb2_grpc.py .

# Copy application source
COPY app/ ./app/

# Model directory — volume-mounted in docker-compose
# If no volume is mounted, model auto-trains on first boot
RUN mkdir -p /app/app/model \
    && chown -R epiguard:epiguard /app

USER epiguard

# Expose HTTP (FastAPI) and gRPC ports
EXPOSE 8000 50051

# Health check — verifies FastAPI is responding
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${HTTP_PORT:-8000}/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]


# ─── Stage 5: trainer ─────────────────────────────────────────────────────────
# Standalone model training image.
# Runs training/train.py, saves epiguard-ai.pkl to /app/app/model/, then exits.
# Never runs the API server.
FROM deps AS trainer

# Copy proto files (needed if training script queries DB via models)
COPY --from=proto-builder /app/triage_pb2.py .
COPY --from=proto-builder /app/triage_pb2_grpc.py .

# Copy full source including training scripts
COPY app/ ./app/
COPY training/ ./training/

RUN mkdir -p /app/app/model /app/reports \
    && chown -R epiguard:epiguard /app

USER epiguard

# Output: /app/app/model/epiguard-ai.pkl + /app/reports/metrics.json
CMD ["python", "-m", "training.train"]


# ─── Stage 6: jupyter ─────────────────────────────────────────────────────────
# Development + EDA environment.
# Includes JupyterLab and optional Phase 2 ML libraries.
# Never used in production.
FROM deps AS jupyter

# Install JupyterLab + EDA extras on top of base deps
RUN pip install --no-cache-dir \
        jupyterlab==4.1.8 \
        ipykernel==6.29.4 \
        ipywidgets==8.1.2 \
        matplotlib==3.8.4 \
        seaborn==0.13.2 \
        plotly==5.21.0 \
        # Phase 2 extras — install now for experimentation
        xgboost==2.0.3 \
        lightgbm==4.3.0 \
        shap==0.45.0

COPY --from=proto-builder /app/triage_pb2.py .
COPY --from=proto-builder /app/triage_pb2_grpc.py .

COPY app/ ./app/
COPY training/ ./training/
COPY notebooks/ ./notebooks/

RUN mkdir -p /app/app/model /app/data /app/notebooks \
    && chown -R epiguard:epiguard /app

USER epiguard

EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--NotebookApp.token=${JUPYTER_TOKEN:-epiguard_dev}", \
     "--notebook-dir=/app/notebooks"]