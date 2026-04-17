# EpiGuard — System Structure

> Complete monorepo layout. Every directory and its purpose.

---

## Root

```
epiguard/
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD — build, test, push, deploy
│
├── proto/
│   └── triage.proto                # gRPC contract (Triage Svc ↔ epiguard-ai)
│
├── scripts/
│   ├── init.sql                    # PostgreSQL schema + seed admin user
│   └── setup.sh                   # VPS bootstrap script (Docker, k8s, env)
│
├── k8s/                            # Kubernetes manifests
│   ├── namespace.yml
│   ├── secrets.yml                 # JWT_SECRET, DB passwords (base64)
│   ├── postgres/
│   │   ├── deployment.yml
│   │   ├── service.yml
│   │   └── pvc.yml                 # Persistent Volume Claim
│   ├── redis/
│   │   ├── deployment.yml
│   │   └── service.yml
│   ├── kafka/
│   │   ├── zookeeper.yml
│   │   ├── kafka.yml
│   │   └── service.yml
│   ├── services/
│   │   ├── api-gateway.yml
│   │   ├── auth-service.yml
│   │   ├── symptom-service.yml
│   │   ├── triage-service.yml
│   │   ├── alert-service.yml
│   │   ├── dashboard-service.yml
│   │   └── epiguard-ai.yml
│   └── ingress/
│       └── ingress.yml             # NGINX ingress + TLS
│
├── docker-compose.yml              # Full local dev stack
├── .env.example                    # Environment variable template
├── .gitignore
├── README.md
└── sys-struct.md                   # ← this file
```

---

## api-gateway

```
api-gateway/
├── src/
│   └── main/
│       ├── java/com/epiguard/gateway/
│       │   ├── config/
│       │   │   ├── GatewayConfig.java          # Route definitions
│       │   │   └── CorsConfig.java
│       │   ├── filter/
│       │   │   ├── JwtAuthFilter.java          # Validates JWT on every request
│       │   │   └── RateLimitFilter.java
│       │   ├── security/
│       │   │   └── JwtUtil.java                # Token parsing (read-only)
│       │   └── GatewayApplication.java
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** Single entry point for all client traffic. Validates JWT, injects `X-User-Id` and `X-User-Role` headers, rate limits, and reverse-proxies to downstream services. No business logic lives here.

---

## auth-service

```
auth-service/
├── src/
│   └── main/
│       ├── java/com/epiguard/auth/
│       │   ├── controller/
│       │   │   └── AuthController.java         # POST /auth/login, /register, /refresh, GET /validate
│       │   ├── service/
│       │   │   └── AuthService.java            # Login, register, token refresh logic
│       │   ├── repository/
│       │   │   └── UserRepository.java
│       │   ├── model/
│       │   │   └── User.java                   # JPA entity — users table
│       │   ├── dto/
│       │   │   └── AuthDto.java                # LoginRequest, RegisterRequest, AuthResponse, ValidateResponse
│       │   ├── security/
│       │   │   ├── JwtUtil.java                # Token generation + validation
│       │   │   ├── JwtFilter.java
│       │   │   └── SecurityConfig.java         # Spring Security stateless config
│       │   └── AuthApplication.java
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** JWT generation (access + refresh), BCrypt password hashing, role-based user registration. Exposes `/auth/validate` as an internal endpoint called by the API Gateway on every request.

---

## symptom-service

```
symptom-service/
├── src/
│   └── main/
│       ├── java/com/epiguard/symptom/
│       │   ├── controller/
│       │   │   └── SymptomController.java      # POST /patients, POST /symptoms
│       │   ├── service/
│       │   │   └── SymptomService.java         # Patient creation + symptom persistence + Kafka publish
│       │   ├── repository/
│       │   │   └── PatientRepository.java
│       │   ├── model/
│       │   │   ├── Patient.java                # patients table
│       │   │   └── Symptom.java                # symptoms table
│       │   ├── dto/
│       │   │   └── SymptomDto.java             # CreatePatientRequest, SubmitSymptomsRequest, responses
│       │   ├── kafka/
│       │   │   ├── SymptomEvent.java           # Kafka message payload
│       │   │   └── SymptomEventProducer.java   # Publishes to symptom-events (partitioned by district)
│       │   └── SymptomApplication.java
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** Creates anonymised patient records (no names). Saves symptoms. Publishes a `SymptomEvent` to Kafka topic `symptom-events` partitioned by district. Returns HTTP 202 Accepted — processing is async downstream.

---

## triage-service

```
triage-service/
├── src/
│   └── main/
│       ├── java/com/epiguard/triage/
│       │   ├── controller/
│       │   │   └── TriageController.java       # GET /triage/{patientId}
│       │   ├── service/
│       │   │   └── TriageService.java          # Kafka consumer + orchestrator
│       │   ├── repository/
│       │   │   └── TriageRepository.java
│       │   ├── model/
│       │   │   └── TriageResult.java           # triage_results table
│       │   ├── dto/
│       │   │   └── TriageDto.java
│       │   ├── kafka/
│       │   │   ├── SymptomEvent.java           # Consumed event shape
│       │   │   └── TriageEvent.java            # Published event shape → triage-events
│       │   ├── grpc/
│       │   │   └── MLServiceGrpcClient.java    # gRPC stub → epiguard-ai:50051
│       │   └── TriageApplication.java
│       ├── proto/
│       │   └── triage.proto                    # Copied from /proto at build time
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** Consumes `symptom-events` from Kafka. Calls **epiguard-ai** via gRPC (`PredictRequest → PredictResponse`). Persists triage result. Publishes `TriageEvent` to `triage-events`. Exposes REST endpoint for frontend to poll results.

---

## alert-service

```
alert-service/
├── src/
│   └── main/
│       ├── java/com/epiguard/alert/
│       │   ├── controller/
│       │   │   └── AlertController.java        # GET /alerts, PATCH /alerts/{id}/resolve
│       │   ├── service/
│       │   │   └── AlertService.java           # Kafka consumer + threshold logic + alert firing
│       │   ├── repository/
│       │   │   └── AlertRepository.java
│       │   ├── model/
│       │   │   └── Alert.java                  # alerts table
│       │   ├── dto/
│       │   │   └── AlertDto.java
│       │   ├── kafka/
│       │   │   └── TriageEvent.java            # Consumed event shape
│       │   └── AlertApplication.java
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** Consumes `triage-events`. Maintains per-district rolling 1-hour case counters (ConcurrentHashMap — replace with Redis in production). When a district hits the configured threshold, creates an Alert record and publishes to `alert-events`. Exposes REST endpoints for officers to view and resolve alerts.

---

## dashboard-service

```
dashboard-service/
├── src/
│   └── main/
│       ├── java/com/epiguard/dashboard/
│       │   ├── controller/
│       │   │   └── DashboardController.java    # GET /dashboard/summary, /dashboard/alerts
│       │   ├── service/
│       │   │   └── DashboardService.java       # Redis-cached aggregation queries
│       │   ├── config/
│       │   │   └── CacheConfig.java            # Redis + Spring Cache configuration
│       │   ├── dto/
│       │   │   └── DashboardDto.java           # SummaryResponse, DistrictSummary, AlertSummary
│       │   └── DashboardApplication.java
│       └── resources/
│           └── application.yml
├── Dockerfile
└── pom.xml
```

**Responsibilities:** Read-heavy service. Serves aggregated summary data to the frontend. Checks Redis first (TTL 5 min) — on cache miss, queries PostgreSQL directly via JdbcTemplate. Scheduled cache eviction every 5 minutes. No Kafka consumer — data flows in via PostgreSQL (written by Triage + Alert services).

---

## epiguard-ai

```
epiguard-ai/
├── app/
│   ├── main.py                     # FastAPI app + startup hooks + gRPC thread launcher
│   ├── grpc_server.py              # MLTriageServicer — implements proto service contract
│   ├── routes/
│   │   └── predict.py              # POST /ml/predict (HTTP fallback / testing)
│   ├── model/
│   │   ├── inference.py            # predict() — load model, build features, run inference
│   │   └── epiguard-ai.pkl         # Serialised trained model (auto-generated on first boot)
│   ├── schemas/
│   │   └── predict.py              # Pydantic request/response models
│   └── utils/
│       └── preprocessing.py        # build_feature_vector() — symptom → numpy array
│
├── proto/
│   └── triage.proto                # gRPC contract (copied from /proto at build time)
│
├── tests/
│   ├── test_inference.py           # Unit tests — model output ranges, priority mapping
│   ├── test_preprocessing.py       # Feature vector shape + normalisation
│   └── test_api.py                 # FastAPI endpoint tests
│
├── requirements.txt                # All Python dependencies (see requirements.txt)
├── Dockerfile                      # Runs protoc codegen + installs deps + starts uvicorn
└── README.md                       # epiguard-ai specific model docs
```

**Responsibilities:** Dual-server — FastAPI on port `8000` (HTTP) and gRPC on port `50051` run concurrently in the same process. On startup, loads `epiguard-ai.pkl` or trains a bootstrap Logistic Regression model and saves it. Converts symptom input into a 14-feature normalised vector and returns `risk_score`, `priority_level`, and `predicted_disease`.

### epiguard-ai model evolution path

```
Phase 1 (MVP)                    Phase 2                        Phase 3
─────────────                    ───────                        ───────
Logistic Regression         →    XGBoost / LightGBM        →   Neural Network
Rule-based clustering       →    DBSCAN geo-clustering      →   Graph-based outbreak detection
No explainability           →    SHAP values               →   Real-time explainability API
Manual model swap           →    MLflow model registry     →   Auto-retraining pipeline
Synthetic training data     →    Real clinic data           →   Federated learning per district
```

---

## Kafka Topics (detail)

```
symptom-events
  Producer  →  symptom-service
  Consumer  →  triage-service (group: triage-group)
  Key       →  district name (for partition locality)
  Payload   →  SymptomEvent { eventId, patientId, age, gender, district, symptoms[], timestamp }

triage-events
  Producer  →  triage-service
  Consumer  →  alert-service (group: alert-group)
               dashboard-service (group: dashboard-group)
  Key       →  district name
  Payload   →  TriageEvent { eventId, patientId, district, riskScore, priorityLevel, predictedDisease, modelVersion, timestamp }

alert-events
  Producer  →  alert-service
  Consumer  →  dashboard-service (group: dashboard-alert-group)
  Key       →  district name
  Payload   →  AlertEvent { alertId, district, alertType, severity, message, timestamp }
```

---

## Database Tables (summary)

```
Table             Primary Key   Key Foreign Keys              Notes
─────────────────────────────────────────────────────────────────────────────
clinics           UUID          —                             District + geo coords
users             UUID          clinic_id → clinics           BCrypt hash, role enum
patients          UUID          clinic_id, submitted_by       No PII — UUID + age + gender + district
symptoms          UUID          patient_id → patients         symptom_type + severity (1–5)
triage_results    UUID          patient_id → patients         risk_score, priority_level, doctor_override
alerts            UUID          —                             district + severity + resolved flag
```

---

## Service Communication Map

```
Client
  │
  ▼ HTTPS
API Gateway
  │
  ├── REST → auth-service       (login, register, token refresh)
  ├── REST → symptom-service    (create patient, submit symptoms)
  ├── REST → triage-service     (get triage result)
  ├── REST → alert-service      (list/resolve alerts)
  └── REST → dashboard-service  (summary, alerts)

symptom-service
  └── Kafka PUBLISH → symptom-events

triage-service
  ├── Kafka CONSUME ← symptom-events
  ├── gRPC CALL    → epiguard-ai:50051
  └── Kafka PUBLISH → triage-events

alert-service
  ├── Kafka CONSUME ← triage-events
  └── Kafka PUBLISH → alert-events

dashboard-service
  ├── Kafka CONSUME ← triage-events   (cache invalidation trigger — optional)
  ├── Kafka CONSUME ← alert-events
  ├── READ          ← PostgreSQL       (on cache miss)
  └── READ/WRITE    ↔ Redis            (5 min TTL cache)

epiguard-ai
  ├── gRPC SERVE   ← triage-service   (port 50051)
  └── HTTP SERVE   ← any caller       (port 8000 — testing/fallback)
```

---

## Environment Variables Reference

```bash
# ── Auth ──────────────────────────────────────────────────────
JWT_SECRET=<min 32 chars — generate with: openssl rand -base64 32>
JWT_EXPIRATION_MS=3600000          # 1 hour
JWT_REFRESH_MS=604800000           # 7 days

# ── Database ──────────────────────────────────────────────────
POSTGRES_PASSWORD=<strong password>
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/epiguard
SPRING_DATASOURCE_USERNAME=epiguard

# ── Redis ─────────────────────────────────────────────────────
REDIS_PASSWORD=<strong password>
SPRING_REDIS_HOST=redis
SPRING_REDIS_PORT=6379

# ── Kafka ─────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# ── epiguard-ai ───────────────────────────────────────────────
ML_SERVICE_HOST=epiguard-ai
ML_SERVICE_GRPC_PORT=50051
GRPC_PORT=50051
HTTP_PORT=8000

# ── Alert thresholds ──────────────────────────────────────────
ALERT_THRESHOLD_CASES_PER_HOUR=20
ALERT_THRESHOLD_CRITICAL_PER_HOUR=40
```

---

## Port Map

| Service | HTTP | gRPC |
|---|---|---|
| api-gateway | 8080 | — |
| auth-service | 8081 | — |
| symptom-service | 8082 | — |
| triage-service | 8083 | — |
| alert-service | 8084 | — |
| dashboard-service | 8085 | — |
| epiguard-ai | 8000 | 50051 |
| PostgreSQL | 5432 | — |
| Redis | 6379 | — |
| Kafka | 9092 (host) / 29092 (internal) | — |
| Kafka UI | 8090 | — |