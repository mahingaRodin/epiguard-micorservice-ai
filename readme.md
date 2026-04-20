<div align="center">

<br/>

```
███████╗██████╗ ██╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██╔════╝██╔══██╗██║██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
█████╗  ██████╔╝██║██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██╔══╝  ██╔═══╝ ██║██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
███████╗██║     ██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚══════╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
```

**AI-Powered Epidemic Risk Prediction & Disease Intelligence Engine**

<br/>

[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![gRPC](https://img.shields.io/badge/gRPC-244c5a?style=for-the-badge&logo=grpc&logoColor=white)](https://grpc.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)

[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square)]()
[![Author](https://img.shields.io/badge/Author-Mahinga_Rodin-blue?style=flat-square)](https://github.com/mahingarodin)

<br/>

> *From raw symptom data to actionable outbreak intelligence — in milliseconds.*

<br/>

</div>

---

## What is epiguard-ai?

**epiguard-ai** is the machine learning core of an epidemic early-warning system. It ingests structured patient symptom data and returns calibrated risk predictions that support clinical triage and public health response — before outbreaks escalate.

The engine answers three questions instantly:

| Question | Output |
|---|---|
| How likely is this an outbreak case? | `risk_score` → 0.0 – 1.0 probability |
| How urgent is this case? | `priority_level` → LOW / MEDIUM / HIGH |
| What disease family is this? | `predicted_disease` → Respiratory / Gastrointestinal / Febrile / Arboviral |

It is designed to run in real clinical environments and exposes two interfaces:

- **gRPC** — primary interface for production, low-latency microservice communication
- **REST API** — secondary interface for testing, integration, and fallback

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│              gRPC (prod)  ─── REST API (dev/fallback)       │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    PREDICTION SERVICE                        │
│          Input validation → Feature engineering             │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      ML INFERENCE CORE                       │
│   StandardScaler  →  Logistic Regression  →  Risk Output    │
│              [epiguard-ai.pkl — 14 features]                 │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                       RESPONSE LAYER                         │
│        risk_score + priority_level + predicted_disease       │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 🔬 Risk Prediction
Supervised ML model evaluates symptom patterns and returns a calibrated risk probability with priority classification.

### 🦠 Disease Clustering
Symptoms are grouped into four disease families: **Respiratory**, **Gastrointestinal**, **Febrile**, and **Arboviral**.

### ⚡ Real-Time Inference
Prediction latency is optimized for live clinical environments. Target: **< 100ms per prediction**, **< 200ms API round-trip**.

### 🤖 Auto-Training Fallback
If no trained model is found at startup, the engine trains a baseline model automatically and stores it for reuse.

---

## Model: Phase 1 — MVP

| Property | Detail |
|---|---|
| Algorithm | Logistic Regression |
| Pipeline | `StandardScaler` → `LogisticRegression` |
| Library | scikit-learn |
| Model File | `models/epiguard-ai.pkl` |
| Input Features | 14 |
| Outputs | `risk_score`, `priority_level`, `predicted_disease` |

### Feature Vector (14 inputs)

All inputs are normalized before inference to ensure consistent model behavior.

| Index | Feature | Normalization |
|---|---|---|
| 0 | age | ÷ 100.0 |
| 1 | gender_encoded | ÷ 2.0 |
| 2 | fever | ÷ 5.0 |
| 3 | cough | ÷ 5.0 |
| 4 | fatigue | ÷ 5.0 |
| 5 | shortness_of_breath | ÷ 5.0 |
| 6 | headache | ÷ 5.0 |
| 7 | diarrhea | ÷ 5.0 |
| 8 | vomiting | ÷ 5.0 |
| 9 | rash | ÷ 5.0 |
| 10 | joint_pain | ÷ 5.0 |
| 11 | chest_pain | ÷ 5.0 |
| 12 | sore_throat | ÷ 5.0 |
| 13 | runny_nose | ÷ 5.0 |

---

## Project Structure

```
epiguard-ai/
│
├── app/
│   ├── api/
│   │   ├── routes.py              # REST prediction endpoint
│   │   └── health.py              # Health check endpoint
│   │
│   ├── grpc/
│   │   ├── server.py              # gRPC server entrypoint
│   │   └── service.py             # gRPC service implementation
│   │
│   ├── models/
│   │   ├── train.py               # Model training pipeline
│   │   ├── predict.py             # Inference logic
│   │   └── model_loader.py        # Model loading + auto-train fallback
│   │
│   ├── services/
│   │   └── prediction_service.py  # Core prediction orchestration
│   │
│   ├── utils/
│   │   └── feature_builder.py     # Symptom → feature vector transformation
│   │
│   └── schemas/
│       └── request_models.py      # Pydantic input/output schemas
│
├── models/
│   └── epiguard-ai.pkl            # Trained model artifact
│
├── notebooks/
│   └── exploratory_analysis.ipynb
│
├── tests/
│   ├── test_prediction.py
│   └── test_features.py
│
├── main.py                        # FastAPI application entrypoint
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip
- virtualenv *(recommended)*

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/mahingarodin/epiguard-ai.git
cd epiguard-ai

python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Service

**Start the REST API server:**
```bash
uvicorn main:app --reload
# → http://localhost:8000
```

**Start the gRPC server:**
```bash
python -m app.grpc.server
# → localhost:50051
```

---

## API Reference

### `POST /ml/predict` — Predict Risk

Submit a patient symptom payload and receive a risk assessment.

**Request:**
```json
{
  "age": 25,
  "gender": "MALE",
  "fever": 3,
  "cough": 2,
  "fatigue": 4,
  "shortness_of_breath": 1,
  "headache": 3,
  "diarrhea": 0,
  "vomiting": 0,
  "rash": 0,
  "joint_pain": 2,
  "chest_pain": 0,
  "sore_throat": 2,
  "runny_nose": 1
}
```

> Symptom severity is scored **0–5** (0 = absent, 5 = severe).

**Response:**
```json
{
  "risk_score": 0.74,
  "priority_level": "HIGH",
  "predicted_disease": "Respiratory"
}
```

---

### `GET /health` — Health Check

Returns the current system readiness state.

```json
{
  "status": "healthy",
  "model_loaded": true
}
```

---

## Model Training

### Train manually:

```bash
python app/models/train.py
```

This will:
1. Train the model on available data
2. Evaluate classification performance
3. Save the trained artifact to `models/epiguard-ai.pkl`

### Evaluation Metrics

Training produces a full evaluation report covering:

- **Accuracy** — overall correct classifications
- **Precision** — correctness of positive predictions
- **Recall** — coverage of true positive cases
- **F1 Score** — harmonic mean of precision and recall

---

## Docker

```bash
# Build
docker build -t epiguard-ai .

# Run (exposes REST + gRPC)
docker run -p 8000:8000 -p 50051:50051 epiguard-ai
```

---

## Testing

```bash
pytest
```

Test coverage includes feature generation, model inference, and API response validation.

---

## Roadmap

### ✅ Phase 1 — MVP *(current)*
- [x] Logistic Regression model
- [x] REST prediction endpoint (`/ml/predict`)
- [x] gRPC prediction endpoint
- [x] Basic disease clustering (4 families)
- [x] Auto-training fallback on startup

### 🔧 Phase 2 — Intelligence Expansion
- [ ] XGBoost model (improved accuracy)
- [ ] LightGBM optimization
- [ ] DBSCAN geographic clustering
- [ ] Prophet time-series forecasting
- [ ] SHAP explainability integration
- [ ] MLflow experiment tracking

### 🚀 Phase 3 — Production AI
- [ ] Automated model retraining pipeline
- [ ] Model version control
- [ ] Prometheus + Grafana monitoring
- [ ] Model performance drift detection
- [ ] Rate limiting + authentication
- [ ] Secure model storage

---

## Security

**Currently implemented:**
- Input schema validation (Pydantic)
- Controlled model loading

**Planned:**
- API authentication
- Rate limiting
- Encrypted model storage

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push and open a pull request

---

## Author

**Mahinga Rodin**  
Rwanda Coding Academy  
[github.com/mahingarodin](https://github.com/mahingarodin)

---

<div align="center">

*Built to detect outbreaks before they escalate.*  
*Accuracy improves as more data becomes available.*

</div>