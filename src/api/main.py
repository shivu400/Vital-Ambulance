"""FastAPI application for the smart ambulance prediction service."""

from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_detector, get_scorer, is_model_ready, load_input
from src.api.middleware import SimpleRateLimiter
from src.api.models import VitalRequest, PredictionResponse, HealthResponse
from src.models.explainability import explain_prediction


app = FastAPI(title="Gray Mobility Smart Ambulance", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SimpleRateLimiter, calls=120, window_seconds=60)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.1.0",
        model_loaded=is_model_ready(),
    )


@app.post("/v1/predict", response_model=PredictionResponse)
def predict(
    payload: VitalRequest,
    detector=Depends(get_detector),
    scorer=Depends(get_scorer),
) -> PredictionResponse:
    data = load_input(payload.model_dump())

    # If model is not trained, we return a safe default
    if not detector.isolation or not detector.ocsvm:
        raise HTTPException(status_code=503, detail="Model not trained yet")

    # Run inference
    df = data.copy()
    y = detector.predict(df)
    scored = scorer.score(df)

    explanation = explain_prediction(df.iloc[0], float(y["anomaly_score"].iloc[0]), bool(y["is_anomaly"].iloc[0]), int(scored["mews_score"].iloc[0]))

    return PredictionResponse(
        is_anomaly=bool(y["is_anomaly"].iloc[0]),
        anomaly_score=float(y["anomaly_score"].iloc[0]),
        confidence=float(y["confidence"].iloc[0]),
        mews_score=int(scored["mews_score"].iloc[0]),
        shock_index=float(scored["shock_index"].iloc[0]),
        clinical_risk=str(scored["clinical_risk"].iloc[0]),
        explanation=explanation["reason"],
    )
