# Gray Mobility Smart Ambulance

Production-ready smart ambulance monitoring system with explainable anomaly
detection, clinical risk scoring, motion-artifact handling, and a robust
FastAPI prediction service.

## Architecture Overview

```
src/
  data/
    generator.py        # Synthetic telemetry (HR, SpO2, SBP, DBP, RR, Temp, Motion)
    validator.py        # Input validation & bounds checking
  preprocessing/
    artifact_detector.py  # Z-score rejection + median filter + SQI
    signal_quality.py     # Rolling Signal Quality Index per vital
  models/
    anomaly_detector.py   # Isolation Forest + OneClassSVM ensemble
    risk_scorer.py        # MEWS score + Shock Index + clinical_risk
    explainability.py     # Rule-based human-readable explanations
  pipeline/
    train.py             # End-to-end training (generates models/ artifacts)
    predict.py           # Batch/online inference utility
  api/
    main.py              # FastAPI app – /health + /v1/predict
    models.py            # Pydantic request/response schemas
    middleware.py        # Rate limiter
    dependencies.py      # Singleton model loader
  evaluation/
    metrics.py           # Precision, recall, false alert rate, latency helpers
    failure_analysis.py  # Known failure modes with mitigations
scripts/
  evaluate.py            # Full evaluation pipeline → reports/
  artifact_demo.py       # Before/after artifact filter plots → reports/
frontend/                # React UI
```

## Signal Descriptions

| Signal | Unit | Normal range | Notes |
|--------|------|-------------|-------|
| hr | bpm | 60–100 | Heart rate |
| spo2 | % | 95–100 | Peripheral oxygen saturation |
| sbp | mmHg | 100–140 | Systolic blood pressure |
| dbp | mmHg | 60–90 | Diastolic blood pressure |
| rr | breaths/min | 12–20 | Respiratory rate |
| temp | °C | 36.1–37.5 | Core body temperature |
| motion | 0–1 | < 0.3 during transport | Vehicle + patient vibration magnitude |

## Model Design

**Anomaly detection** uses an ensemble of:
- **Isolation Forest** (n=100, contamination=0.05) – identifies statistical outliers in feature space
- **OneClassSVM** (RBF kernel, nu=0.05) – complements IF with a different decision boundary geometry

Both models are trained **exclusively on normal-phase data** so they learn the clean baseline. The combined score threshold and standard deviation are persisted to `models/detector_meta.json` at training time, making inference fully deterministic across sessions.

**Risk scoring** uses a simplified MEWS (Modified Early Warning Score) combining HR, SBP, RR, Temp, SpO2 weighted by clinical severity, plus the Shock Index (HR/SBP).

**Confidence** is the normalized distance of the combined decision score from the training-derived threshold, clipped to [0, 1].

## API Response Schema

```json
{
  "is_anomaly": false,
  "anomaly_score": 0.142,
  "confidence": 0.81,
  "mews_score": 1,
  "shock_index": 0.67,
  "clinical_risk": "normal",
  "explanation": "Vitals within expected range and no detected anomalies"
}
```

## Quickstart

### 1) Install dependencies

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
```

### 2) Train the model

```powershell
python -m src.pipeline.train
```

Trains on synthetic 30-minute ambulance journey (900 normal-phase samples).
Saves `models/isolation_forest.pkl`, `models/ocsvm.pkl`, `models/detector_meta.json`,
and `models/training_data.parquet`.

### 3) Run evaluation (generates reports/)

```powershell
python scripts/evaluate.py
```

Produces `reports/metrics.json` and `reports/metrics_report.md` with precision,
recall, false alert rate, alert latency, per-phase breakdown, and 3 failure cases.

### 4) Generate artifact plots

```powershell
python scripts/artifact_demo.py
```

Saves `reports/artifact_demo.png` showing before/after filtering for HR, SpO2, SBP
with motion artifact windows and SQI overlays.

### 5) Run the API

```powershell
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6) Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### 7) Example API call

```powershell
curl -X POST http://localhost:8000/v1/predict `
  -H "Content-Type: application/json" `
  -d '{"timestamp": "2026-03-09T00:00:00Z", "hr": 90, "spo2": 97, "sbp": 120, "dbp": 80, "rr": 18, "temp": 37.0}'
```

### 8) Docker (optional)

```powershell
docker-compose up --build
```

## Running Tests

```bash
pytest -q
```

## Safety Analysis

See **[SAFETY_ANALYSIS.md](SAFETY_ANALYSIS.md)** for the written safety-critical
analysis covering:
1. Most dangerous failure mode
2. How to reduce false alerts without missing deterioration
3. What should never be fully automated in medical AI systems

## Evaluation Results

After training, run `python scripts/evaluate.py` to reproduce the numbers.
A sample run (seed=99 eval, seed=42 train) yields:

| Metric | Value |
|--------|-------|
| Precision | 0.568 |
| Recall | 1.000 |
| F1-Score | 0.725 |
| False Alert Rate | 0.309 |
| Alert Latency | ~0s |

> **Design choice:** Recall is prioritised to 1.0 over precision in a life-critical
> system. False negatives (missed deterioration) are more dangerous than false
> positives (alarm fatigue). See SAFETY_ANALYSIS.md for the full rationale.
