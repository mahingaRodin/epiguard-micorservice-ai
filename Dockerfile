Copy

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
 