# Forecast-Bust Sentinel

> **Know When Forecasts May Fail**: An AI-powered sentinel service designed to analyze already-issued medium-range weather forecasts and estimate how likely they are to fail unusually badly ("forecast bust").

---

## 🏗️ Architecture & Roles

```
Existing Forecast ──► Weather Data Pipeline ──► Feature Engineering ──► Calibrated ML Model ──► Safety / Abstention ──► Explanation / Evidence ──► Backend API ──► Frontend
```

### Role Separation:
* **Builder 1 (Backend & Orchestration)**:
  * FastAPI Application (`/v1/health`, `/v1/predict`, `/docs`)
  * Pydantic Request & Response Schemas
  * `ForecastBustAgent` Orchestrator
  * Service Interfaces (`BaseWeatherService`, `BaseFeatureService`, `BaseModelService`)
  * Safety, Out-Of-Distribution (OOD), & Abstention Engine
  * Backend Testing Suite

* **Builder 2 (Data & ML Pipeline - Separate)**:
  * Weather Data Ingestion (GEFS, ERA5, ECMWF)
  * Feature Engineering & Preprocessing
  * Bust Label Generation
  * ML Model Training (LightGBM / XGBoost)
  * Probability Calibration
  * Model Artifacts

---

## 🚀 Quickstart

### 1. Prerequisites & Installation
Ensure Python 3.10+ is installed.

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```

Once started:
* **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Interactive Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Endpoint**: [http://localhost:8000/v1/health](http://localhost:8000/v1/health)
* **Predict Endpoint**: `POST http://localhost:8000/v1/predict`

### 3. Run Automated Tests
```bash
pytest backend/tests -v
```

---

## 📡 API Contract

### Health Check: `GET /v1/health`
**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "forecast-bust-sentinel",
  "version": "0.1.0"
}
```

### Predict Forecast Bust: `POST /v1/predict`
**Request Payload:**
```json
{
  "location": "London",
  "target_date": "2026-09-01"
}
```

**Safe Abstain Response (While Builder-2 Model is in Development):**
```json
{
  "location": "London",
  "bust_probability": null,
  "risk_level": null,
  "trust_state": "UNAVAILABLE",
  "abstain": true,
  "reason_codes": [
    "MODEL_NOT_READY"
  ],
  "model_version": null,
  "data_version": null
}
```

---

## 🔌 Builder 2 Integration Points

Builder 2 components can be plugged in by implementing the abstract base classes in `backend/app/services/base.py`:

```python
from backend.app.services.base import BaseModelService, FeatureResult, ModelResult

class CalibratedGBMModelService(BaseModelService):
    def predict(self, feature_result: FeatureResult) -> ModelResult:
        # 1. Run LightGBM / XGBoost model
        # 2. Calibrate probability (Isotonic / Platt scaling)
        return ModelResult(
            probability=calibrated_prob,
            model_version="lgbm-bust-v1.0",
            is_ready=True,
            metadata={"brier_score": 0.082}
        )
```

Pass the service into `ForecastBustAgent(model_service=CalibratedGBMModelService())` or register it in the dependency injection container.
