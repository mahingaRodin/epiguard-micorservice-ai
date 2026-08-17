import logging
import threading
from concurrent import futures
from pathlib import Path

import grpc
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.model.inference import is_model_loaded, load_model
from app.routes.metrics import router as metrics_router
from app.routes.predict import router as predict_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="EpiGuard AI — ML Triage Engine",
    description=(
        "Machine learning service for epidemic triage. "
        "Submit patient symptoms to receive a risk score, priority level, "
        "and predicted disease cluster.\n\n"
        "**Demo:** [Interactive triage demo](/) · "
        "**Swagger UI:** [/docs](/docs) · "
        "**ReDoc:** [/redoc](/redoc)"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "EpiGuard Platform",
        "url": "http://4.168.192.169/",
    },
    license_info={
        "name": "Internal use",
    },
    openapi_tags=[
        {"name": "Health", "description": "Service health and readiness"},
        {"name": "Prediction", "description": "ML triage prediction endpoints"},
        {"name": "Monitoring", "description": "Prometheus metrics"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router, prefix="/ml")
app.include_router(metrics_router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
async def startup():
    load_model()
    logger.info("epiguard-ai model loaded")
    thread = threading.Thread(target=_start_grpc_server, daemon=True)
    thread.start()
    logger.info("gRPC server thread started on port %d", settings.grpc_port)


@app.get("/", include_in_schema=False)
def demo_page():
    index = STATIC_DIR / "demo" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "EpiGuard AI is running", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "up",
        "service": "epiguard-ai",
        "version": "1.0.0",
        "model_loaded": is_model_loaded(),
    }


def _start_grpc_server():
    try:
        from app.grpc_server import MLTriageServicer, add_MLTriageServiceServicer_to_server

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_MLTriageServiceServicer_to_server(MLTriageServicer(), server)
        server.add_insecure_port(f"[::]:{settings.grpc_port}")
        server.start()
        logger.info("gRPC server listening on port %d", settings.grpc_port)
        server.wait_for_termination()
    except ImportError as e:
        logger.warning("gRPC server not started — proto files missing: %s", e)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.http_port, reload=False)
