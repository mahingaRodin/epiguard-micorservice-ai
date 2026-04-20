# epiguard-ai — Machine Learning Engine TO_DO

Legend:
[ ] Not started  
[~] In progress  
[x] Completed  
[!] Blocked  

---

# 0 — PROJECT INITIALIZATION

## Core Setup

[ ] Create Python virtual environment  
[ ] Install dependencies  
[ ] Create `requirements.txt`  
[ ] Create `.env.example`  
[ ] Setup logging configuration  
[ ] Setup configuration management (`settings.py`)

Dependencies:

[ ] fastapi  
[ ] uvicorn  
[ ] scikit-learn  
[ ] numpy  
[ ] pandas  
[ ] joblib  
[ ] grpcio  
[ ] grpcio-tools  

Optional:

[ ] matplotlib  
[ ] seaborn  
[ ] mlflow  
[ ] shap  

---

# 1 — PROJECT STRUCTURE

Verify folder structure exists:

[ ] app/
[ ] app/api/
[ ] app/grpc/
[ ] app/models/
[ ] app/services/
[ ] app/utils/
[ ] app/data/
[ ] app/tests/
[ ] models/
[ ] notebooks/

Files:

[ ] main.py  
[ ] predict.py  
[ ] train.py  
[ ] feature_builder.py  
[ ] model_loader.py  
[ ] health.py  

---

# 2 — DATA PIPELINE

## Dataset Preparation

[ ] Collect initial training dataset  
[ ] Validate dataset schema  
[ ] Handle missing values  
[ ] Normalize symptom scales  
[ ] Encode categorical variables  

Required Features:

[ ] age  
[ ] gender  
[ ] fever  
[ ] cough  
[ ] fatigue  
[ ] shortness_of_breath  
[ ] headache  
[ ] diarrhea  
[ ] vomiting  
[ ] rash  
[ ] joint_pain  
[ ] chest_pain  
[ ] sore_throat  
[ ] runny_nose  

Validation:

[ ] Value range validation  
[ ] Outlier detection  
[ ] Dataset splitting  

Split:

[ ] Training set  
[ ] Validation set  
[ ] Test set  

---

# 3 — FEATURE ENGINEERING

Feature Vector Builder

[ ] Normalize age  
[ ] Encode gender  
[ ] Normalize symptom scores  
[ ] Build fixed-length vector  
[ ] Validate vector size (14)

Functions:

[ ] build_feature_vector()  
[ ] validate_feature_vector()  

Testing:

[ ] Unit test feature builder  
[ ] Input validation test  

---

# 4 — MVP MODEL — LOGISTIC REGRESSION

Core Model

[ ] Create StandardScaler pipeline  
[ ] Train Logistic Regression model  
[ ] Evaluate model accuracy  
[ ] Save trained model  

Evaluation:

[ ] Accuracy score  
[ ] Precision  
[ ] Recall  
[ ] F1-score  

Persistence:

[ ] Save model → `epiguard-ai.pkl`  
[ ] Load model from disk  
[ ] Auto-train if model missing  

Testing:

[ ] Model load test  
[ ] Prediction test  

---

# 5 — DISEASE CLUSTERING (RULE-BASED)

Symptom Mapping

Clusters:

[ ] Respiratory  
[ ] Gastrointestinal  
[ ] Febrile  
[ ] Arboviral  

Implementation:

[ ] Symptom rule mapping  
[ ] Cluster detection logic  

Testing:

[ ] Cluster classification test  

---

# 6 — PREDICTION SERVICE (CORE LOGIC)

Prediction Pipeline

[ ] Load model  
[ ] Receive symptom input  
[ ] Build feature vector  
[ ] Generate prediction  
[ ] Assign priority level  

Priority Logic:

[ ] LOW  
[ ] MEDIUM  
[ ] HIGH  

Output Format:

[ ] risk_score  
[ ] priority_level  
[ ] predicted_disease  

Testing:

[ ] End-to-end prediction test  

---

# 7 — FASTAPI SERVER

Core API

[ ] Initialize FastAPI app  
[ ] Setup routing  
[ ] Add middleware  

Endpoints:

[ ] POST /ml/predict  
[ ] GET /health  

Validation:

[ ] Request schema validation  
[ ] Response schema validation  

Testing:

[ ] API endpoint test  
[ ] Error handling test  

---

# 8 — gRPC SERVER

Communication Layer

[ ] Define proto file  
[ ] Generate gRPC code  
[ ] Implement gRPC server  
[ ] Implement prediction handler  

Testing:

[ ] gRPC request test  
[ ] Response validation  

Integration:

[ ] Test connection with triage-service  

---

# 9 — MODEL VERSIONING

Version Control

[ ] Add model version metadata  
[ ] Track training parameters  
[ ] Save training logs  

Optional:

[ ] MLflow integration  
[ ] Model registry setup  

---

# 10 — MODEL MONITORING

Performance Tracking

[ ] Track prediction latency  
[ ] Track prediction counts  
[ ] Track error rates  

Metrics:

[ ] Average latency  
[ ] Failed predictions  
[ ] Model usage frequency  

---

# 11 — PHASE 2 — ADVANCED MODELS

## Gradient Boosting Models

[ ] Implement XGBoost  
[ ] Implement LightGBM  
[ ] Compare performance  
[ ] Select best model  

Evaluation:

[ ] Accuracy comparison  
[ ] Performance benchmarking  

---

## Clustering — Geographic Detection

[ ] Implement DBSCAN  
[ ] Add geographic coordinates  
[ ] Detect outbreak zones  

Testing:

[ ] Cluster visualization  

---

## Forecasting

[ ] Implement Prophet  
[ ] Train district models  
[ ] Predict case trends  

Testing:

[ ] Forecast validation  

---

## Explainability

[ ] Install SHAP  
[ ] Generate SHAP values  
[ ] Add prediction explanation  

---

# 12 — MODEL RETRAINING PIPELINE

Automation

[ ] Create retraining script  
[ ] Schedule retraining job  
[ ] Validate updated models  

Testing:

[ ] Retraining workflow test  

---

# 13 — TESTING

Unit Tests:

[ ] Feature builder  
[ ] Model loader  
[ ] Prediction logic  

Integration Tests:

[ ] FastAPI prediction  
[ ] gRPC prediction  

System Tests:

[ ] Full prediction flow  

---

# 14 — PERFORMANCE OPTIMIZATION

Speed:

[ ] Optimize inference time  
[ ] Reduce model load latency  

Memory:

[ ] Optimize memory usage  

Benchmark:

[ ] Measure response time  

---

# 15 — SECURITY

Input Security:

[ ] Validate all input fields  
[ ] Prevent malformed data  

Model Security:

[ ] Restrict model file access  

API Security:

[ ] Rate limiting  
[ ] Request size limits  

---

# 16 — DOCKERIZATION

Container Setup

[ ] Create Dockerfile  
[ ] Install dependencies  
[ ] Copy model files  
[ ] Expose ports  

Testing:

[ ] Build image  
[ ] Run container  
[ ] Health check test  

---

# 17 — DEPLOYMENT READINESS

Configuration:

[ ] Environment variables setup  
[ ] Configurable ports  

Health:

[ ] Health check readiness  

Testing:

[ ] Production simulation  

---

# 18 — DOCUMENTATION

[ ] Model documentation  
[ ] API documentation  
[ ] gRPC documentation  
[ ] Training documentation  

---

# CURRENT TASKS

Daily working list.

- [ ] _________________________  
- [ ] _________________________  
- [ ] _________________________  

---

# BLOCKERS

Issues slowing development.

- [ ] _________________________  

---

# NEXT MILESTONE

Example:

Train MVP Logistic Regression Model

_________________________

---

# NOTES

Ideas, improvements, reminders.

- _________________________  
- _________________________  
- _________________________  
