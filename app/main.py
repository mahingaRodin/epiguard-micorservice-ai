import logging
import threading
from concurrent import futures

import grpc
import uvicorn
from fastapi import FastAPI

from app.config.settings import settings
from app.model.inference import load_model
from app.routes.predict import router as predict_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="epiguard-ai",
    description="EpiGuard ML triage and outbreak intelligence engine",
    version="1.0.0",
)

app.include_router(predict_router, prefix="/ml")


@app.on_event("startup")
async def startup():
    load_model()
    logger.info("epiguard-ai model loaded")
    thread = threading.Thread(target=_start_grpc_server, daemon=True)
    thread.start()
    logger.info("gRPC server thread started on port %d", settings.grpc_port)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "up", "service": "epiguard-ai", "version": "1.0.0"}


def _start_grpc_server():
    # Import here — proto files generated at Docker build time
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
