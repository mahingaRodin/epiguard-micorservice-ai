<div align="center">

# EpiGuard

**Real-Time National Epidemic Intelligence & Outbreak Detection System**

[![Java](https://img.shields.io/badge/Java_17-1a202c?style=flat&logo=openjdk&logoColor=ed8b00)](https://openjdk.org/)
[![Python](https://img.shields.io/badge/Python_3.11-1a202c?style=flat&logo=python&logoColor=3776ab)](https://python.org/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot_3.2-1a202c?style=flat&logo=spring-boot&logoColor=6db33f)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-1a202c?style=flat&logo=fastapi&logoColor=009688)](https://fastapi.tiangolo.com/)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-1a202c?style=flat&logo=apache-kafka&logoColor=white)](https://kafka.apache.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1a202c?style=flat&logo=kubernetes&logoColor=326ce5)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/Docker-1a202c?style=flat&logo=docker&logoColor=2496ed)](https://docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-1a202c?style=flat&logo=postgresql&logoColor=336791)](https://postgresql.org/)

*Detect outbreaks before they escalate — event-driven, AI-powered, nationally scalable.*

</div>

---

## What is EpiGuard?

EpiGuard is a distributed real-time health intelligence platform built for national-scale epidemic surveillance. Community health workers submit patient symptom data from clinics across Rwanda. That data streams through event pipelines, gets scored by **epiguard-ai** (the integrated ML triage engine), and surfaces as live outbreak intelligence on dashboards used by district officers and national health administrators.

When a district crosses a configurable case threshold within a rolling time window, EpiGuard fires an automated outbreak alert — before the situation escalates.

---

## System Architecture

```
                        ┌─────────────────────┐
                        │    React Frontend    │
                        │  TypeScript + WS     │
                        └────────┬────────────┘
                                 │ HTTPS
                        ┌────────▼────────────┐
                        │    API Gateway       │
                        │  JWT · Routing       │
                        └──┬──┬──┬──┬──┬──────┘
                           │  │  │  │  │
          ┌────────────────┘  │  │  │  └──────────────────┐
          │               ┌───┘  └───┐                     │
          ▼               ▼          ▼                     ▼
    ┌──────────┐   ┌───────────┐ ┌──────────┐   ┌─────────────────┐
    │   Auth   │   │  Symptom  │ │ Triage   │   │   Dashboard     │
    │  Service │   │  Service  │ │ Service  │   │   Service       │
    └──────────┘   └─────┬─────┘ └────┬─────┘   └────────┬────────┘
                         │            │  gRPC             │
                    ┌────▼────────────▼───────────────────▼────┐
                    │           Apache Kafka Event Bus          │
                    │  symptom-events · triage-events ·         │
                    │  alert-events  (partitioned by district)  │
                    └────────────────┬──────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │    Alert Service     │
                          │  Threshold detection │
                          └──────────┬──────────┘
                                     │ gRPC
                          ┌──────────▼──────────┐
                          │    epiguard-ai       │
                          │  FastAPI · Python    │
                          │  scikit-learn model  │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │           Data Layer            │
                    │    PostgreSQL 16 · Redis 7      │
                    └─────────────────────────────────┘
```

---

## Microservices

| Service | Language | Port | Role |
|---|---|---|---|
| `api-gateway` | Java · Spring Boot | `8080` | Single entry point — JWT validation, rate limiting, routing |
| `auth-service` | Java · Spring Boot | `8081` | Login, registration, JWT issue & refresh |
| `symptom-service` | Java · Spring Boot | `8082` | Patient creation, symptom submission, Kafka producer |
| `triage-service` | Java · Spring Boot | `8083` | Kafka consumer → calls epiguard-ai via gRPC → stores results |
| `alert-service` | Java · Spring Boot | `8084` | Rolling-window threshold detection, outbreak alert generation |
| `dashboard-service` | Java · Spring Boot | `8085` | Read-optimised aggregations, Redis-cached summaries |
| `epiguard-ai` | Python · FastAPI | `8000` / `50051` | ML risk scoring + disease clustering — HTTP + gRPC |

---

## epiguard-ai — The ML Engine

epiguard-ai is EpiGuard's embedded intelligence layer. It receives patient symptom vectors from the Triage Service over gRPC and returns a structured risk prediction.

### Phase 1 — MVP model
| Property | Detail |
|---|---|
| Algorithm | Logistic Regression (scikit-learn pipeline with StandardScaler) |
| Input features | Age (normalised), gender (encoded), 12 symptom severity scores |
| Output | `risk_score` (0.0–1.0), `priority_level` (LOW / MEDIUM / HIGH), `predicted_disease` |
| Model file | `epiguard-ai.pkl` — auto-trained on first boot if not present |
| Disease clustering | Rule-based symptom co-occurrence: Respiratory, GI, Febrile, Arboviral |
| Transport | gRPC port `50051` (primary) + REST `/ml/predict` (HTTP fallback / testing) |

### Phase 2 — Advanced
- XGBoost / LightGBM for improved accuracy on imbalanced outbreak data
- DBSCAN geographic clustering for spatial outbreak zone detection
- Facebook Prophet for district-level case forecasting
- SHAP values for explainability — why was this case flagged HIGH?
- MLflow for experiment tracking and model versioning

### Feature vector layout (length: 14)
```
Index  Feature
  0    age / 100.0
  1    gender_encoded / 2.0       MALE=0, FEMALE=1, OTHER=2
  2    fever / 5.0
  3    cough / 5.0
  4    fatigue / 5.0
  5    shortness_of_breath / 5.0
  6    headache / 5.0
  7    diarrhea / 5.0
  8    vomiting / 5.0
  9    rash / 5.0
 10    joint_pain / 5.0
 11    chest_pain / 5.0
 12    sore_throat / 5.0
 13    runny_nose / 5.0
```

---

## Kafka Topics

| Topic | Partitioned by | Producer | Consumer(s) |
|---|---|---|---|
| `symptom-events` | district | `symptom-service` | `triage-service` |
| `triage-events` | district | `triage-service` | `alert-service`, `dashboard-service` |
| `alert-events` | district | `alert-service` | `dashboard-service` |

---

## User Roles

| Role | Scope | Capabilities |
|---|---|---|
| CHW | Clinic | Submit symptoms, view own patient triage results |
| Doctor | Clinic | View all clinic patients, confirm or override AI triage |
| District Officer | District | Monitor outbreaks, view regional trends, receive alerts |
| Admin | National | Full system access — user management, all dashboards, configs |

---

## Database Schema

```
clinics ──< users
clinics ──< patients
users   ──< patients  (submitted_by)
patients ──< symptoms
patients ──1 triage_results
alerts   (standalone — triggered by district threshold logic)
```

Key design decisions:
- **No PII stored** — patients are UUID + age + gender + district only
- All tables use UUID primary keys (`uuid-ossp`)
- Indexes on `district`, `created_at`, `priority_level` for dashboard query performance
- Enums enforced at DB level (`user_role`, `priority_level`, `alert_severity`)

---

## Getting Started

### Prerequisites
- Docker Desktop
- Java 17+
- Python 3.11+
- Maven 3.9+

### 1. Clone

```bash
git clone https://github.com/mahingarodin/epiguard.git
cd epiguard
```

### 2. Environment

```bash
cp .env.example .env
# Set: JWT_SECRET (min 32 chars), POSTGRES_PASSWORD, REDIS_PASSWORD
```

Generate a secure JWT secret:
```bash
openssl rand -base64 32
```

### 3. Full stack with Docker Compose

```bash
docker-compose up --build
```

### 4. Verify everything is running

```bash
# Login as default admin
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@epiguard.rw","password":"Admin@1234"}'

# epiguard-ai health
curl http://localhost:8000/health

# Kafka UI
open http://localhost:8090
```

---

## API Reference

### Auth Service
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login` | None | Login, returns JWT tokens |
| `POST` | `/auth/register` | None | Register new user |
| `POST` | `/auth/refresh` | Refresh token | Refresh access token |
| `GET` | `/auth/validate` | Bearer | Internal — gateway token validation |

### Symptom Service
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/patients` | CHW+ | Create anonymised patient record |
| `POST` | `/symptoms` | CHW+ | Submit symptoms — triggers Kafka → triage pipeline |

### Triage Service
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/triage/{patientId}` | DOCTOR+ | Get latest triage result |

### Dashboard Service
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/summary` | OFFICER+ | Nationwide case counts + per-district breakdown |
| `GET` | `/dashboard/alerts` | OFFICER+ | Active unresolved alerts |

### Alert Service
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/alerts` | OFFICER+ | List all active alerts |
| `PATCH` | `/alerts/{id}/resolve` | OFFICER+ | Mark alert as resolved |

### epiguard-ai (direct)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/ml/predict` | None | HTTP prediction endpoint (testing / fallback) |
| `GET` | `/health` | None | Model status + version |

---

## Deployment

### Kubernetes
```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/kafka/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/

kubectl get pods -n epiguard
```

### CI/CD Pipeline (GitHub Actions)
```
Push to main
     │
     ▼
Run tests (mvn test + pytest)
     │
     ▼
Build Docker images
     │
     ▼
Push → Docker Hub (mahingarodin/epiguard-*)
     │
     ▼
SSH → VPS → kubectl rollout restart
     │
     ▼
Health check all pods
```

---

## Environment Variables

| Variable | Used by | Description |
|---|---|---|
| `JWT_SECRET` | All Java services | Min 32-char secret for JWT signing |
| `JWT_EXPIRATION_MS` | Auth | Access token TTL (default `3600000` = 1h) |
| `POSTGRES_PASSWORD` | All + PostgreSQL | Database password |
| `REDIS_PASSWORD` | Dashboard + Redis | Cache password |
| `KAFKA_BOOTSTRAP_SERVERS` | Symptom, Triage, Alert | Kafka broker address |
| `ML_SERVICE_HOST` | Triage | epiguard-ai hostname |
| `ML_SERVICE_GRPC_PORT` | Triage | epiguard-ai gRPC port (default `50051`) |
| `ALERT_THRESHOLD_CASES_PER_HOUR` | Alert | HIGH alert trigger (default `20`) |
| `ALERT_THRESHOLD_CRITICAL_PER_HOUR` | Alert | CRITICAL alert trigger (default `40`) |
| `GRPC_PORT` | epiguard-ai | gRPC server port (default `50051`) |

---

## Security

| Control | Implementation |
|---|---|
| Authentication | JWT HS256 — 1h access token, 7d refresh token |
| Authorisation | Role-based access control at gateway + service level |
| Passwords | BCrypt cost factor 12 |
| Transport | HTTPS everywhere — TLS termination at k8s ingress |
| Patient privacy | Zero PII — no names stored anywhere in the system |
| Kafka | Topic access by service identity |

---

## Project Status

| Phase | Status |
|---|---|
| Backend services (7 services) | ✅ Complete |
| epiguard-ai Phase 1 (LR model) | ✅ Complete |
| Database schema + migrations | ✅ Complete |
| Kafka pipeline (3 topics) | ✅ Complete |
| Docker + Kubernetes | 🔄 In progress |
| CI/CD GitHub Actions | 🔄 In progress |
| Frontend (React + TypeScript) | ⏳ Planned |
| epiguard-ai Phase 2 (XGBoost, DBSCAN, Prophet) | ⏳ Planned |

---

## Author

**Mahinga Rodin** — Rwanda Coding Academy

[![LinkedIn](https://img.shields.io/badge/LinkedIn-1a202c?style=flat&logo=linkedin&logoColor=0a66c2)](https://linkedin.com/in/mahinga-rodin)
[![GitHub](https://img.shields.io/badge/GitHub-1a202c?style=flat&logo=github&logoColor=white)](https://github.com/mahingarodin)
[![Email](https://img.shields.io/badge/Email-1a202c?style=flat&logo=gmail&logoColor=ea4335)](mailto:mahingarodin@gmail.com)

---

<div align="center">
  <sub>Built with Java, Python, Kafka, and a genuine need to detect outbreaks early.</sub>
</div>