"""Pydantic request and response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VitalRequest(BaseModel):
    timestamp: datetime = Field(..., description="UTC timestamp of the measurement")
    hr: float = Field(..., ge=1, le=250, description="Heart rate (bpm)")
    spo2: float = Field(..., ge=50, le=100, description="Oxygen saturation (%)")
    sbp: float = Field(..., ge=40, le=250, description="Systolic blood pressure (mmHg)")
    dbp: float = Field(..., ge=20, le=160, description="Diastolic blood pressure (mmHg)")
    rr: float = Field(..., ge=4, le=60, description="Respiratory rate (breaths / min)")
    temp: float = Field(..., ge=30, le=43, description="Core temperature (°C)")


class PredictionResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in the anomaly decision (0–1)")
    mews_score: int
    shock_index: float
    clinical_risk: str
    explanation: str


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
