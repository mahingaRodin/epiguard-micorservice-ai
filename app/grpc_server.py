"""
gRPC servicer — implements MLTriageService from triage.proto.
Proto-generated files (triage_pb2.py, triage_pb2_grpc.py) are created
at Docker build time via grpc_tools.protoc.
"""
import logging
from app.model.inference import predict

logger = logging.getLogger(__name__)

try:
    import triage_pb2 as pb2
    import triage_pb2_grpc as pb2_grpc

    class MLTriageServicer(pb2_grpc.MLTriageServiceServicer):
        def Predict(self, request, context):
            symptoms = [
                {"symptom_type": s.symptom_type, "severity": s.severity}
                for s in request.symptoms
            ]
            result = predict(
                patient_id=request.patient_id,
                age=request.age,
                gender=request.gender,
                district=request.district,
                symptoms=symptoms,
            )
            return pb2.PredictResponse(
                risk_score=result["risk_score"],
                priority_level=result["priority_level"],
                predicted_disease=result["predicted_disease"],
                model_version=result["model_version"],
            )

    add_MLTriageServiceServicer_to_server = pb2_grpc.add_MLTriageServiceServicer_to_server

except ImportError:
    logger.warning("Proto-generated files not found — run protoc first.")

    class MLTriageServicer:
        pass

    def add_MLTriageServiceServicer_to_server(servicer, server):
        pass
