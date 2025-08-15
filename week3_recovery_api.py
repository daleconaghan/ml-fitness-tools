"""
Week 3: Recovery API - HTTP endpoints for ML fitness predictions
Serves RPE calculations and strength predictions via REST API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import numpy as np
from datetime import datetime, date
import uvicorn

# Load existing models/data
with open('training_data.json', 'r') as f:
    training_data = json.load(f)

app = FastAPI(
    title="ML Fitness Tools API",
    description="API for RPE calculations and strength predictions",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class RPERequest(BaseModel):
    weight: float
    reps: int
    rpe: float
    exercise: str = "squat"

class RPEResponse(BaseModel):
    adjusted_volume: float
    training_stress: float
    recommendation: str
    rpe_efficiency: float

class StrengthRequest(BaseModel):
    recent_sessions: List[Dict]
    target_reps: int = 5
    exercise: str = "squat"

class StrengthResponse(BaseModel):
    predicted_weight: float
    confidence: float
    next_workout: Dict
    progression: str

class RecoveryRequest(BaseModel):
    last_session_rpe: float
    hours_since_training: float
    sleep_quality: float  # 1-10 scale
    stress_level: float   # 1-10 scale
    muscle_soreness: float  # 1-10 scale

class RecoveryResponse(BaseModel):
    recovery_score: float  # 0-100%
    recommended_intensity: float  # RPE 1-10
    training_readiness: str
    recommendations: List[str]

# RPE Calculator (from Week 1)
def calculate_rpe_metrics(weight: float, reps: int, rpe: float) -> Dict:
    """Calculate RPE-based training metrics"""
    # RPE to percentage conversion (simplified Helms RPE chart)
    rpe_to_percent = {
        10: 100, 9.5: 97, 9: 94, 8.5: 91, 8: 88,
        7.5: 85, 7: 82, 6.5: 79, 6: 76
    }
    
    intensity_percent = rpe_to_percent.get(rpe, 70)
    estimated_1rm = weight / (intensity_percent / 100)
    
    # Volume calculation
    base_volume = weight * reps
    rpe_multiplier = 0.5 + (rpe / 10) * 0.5  # RPE affects volume quality
    adjusted_volume = base_volume * rpe_multiplier
    
    # Training stress (simplified TSS-like metric)
    training_stress = (intensity_percent * base_volume) / 100
    
    # RPE efficiency (lower RPE = higher efficiency for same volume)
    rpe_efficiency = (10 - rpe) / 10
    
    return {
        "adjusted_volume": round(adjusted_volume, 2),
        "training_stress": round(training_stress, 2),
        "rpe_efficiency": round(rpe_efficiency, 2),
        "estimated_1rm": round(estimated_1rm, 2)
    }

# Strength Predictor (from Week 2)
def predict_next_strength(sessions: List[Dict], target_reps: int = 5) -> Dict:
    """Predict next workout strength based on recent sessions"""
    if not sessions:
        raise ValueError("No training data provided")
    
    # Extract weights and create simple linear progression
    weights = [session.get('weight', 0) for session in sessions[-5:]]  # Last 5 sessions
    
    if len(weights) < 2:
        # If insufficient data, use conservative progression
        last_weight = weights[0] if weights else 100
        predicted_weight = last_weight * 1.025  # 2.5% increase
        confidence = 50.0
    else:
        # Linear regression for trend
        x = np.array(range(len(weights)))
        y = np.array(weights)
        
        # Simple linear fit
        slope = np.sum((x - np.mean(x)) * (y - np.mean(y))) / np.sum((x - np.mean(x))**2)
        intercept = np.mean(y) - slope * np.mean(x)
        
        # Predict next session
        next_x = len(weights)
        predicted_weight = slope * next_x + intercept
        
        # Calculate confidence based on consistency
        consistency = 1 / (1 + np.std(weights))
        confidence = min(95.0, max(60.0, consistency * 100))
    
    return {
        "predicted_weight": round(predicted_weight, 1),
        "confidence": round(confidence, 1),
        "trend": "increasing" if len(weights) > 1 and weights[-1] > weights[0] else "stable"
    }

# New Recovery Algorithm (Week 3)
def calculate_recovery_score(last_rpe: float, hours_since: float, sleep: float, 
                           stress: float, soreness: float) -> Dict:
    """Calculate recovery score and training readiness"""
    
    # Recovery factors (weighted)
    time_recovery = min(100, (hours_since / 48) * 100)  # Full recovery in 48h
    sleep_recovery = (sleep / 10) * 100
    stress_recovery = ((10 - stress) / 10) * 100
    soreness_recovery = ((10 - soreness) / 10) * 100
    rpe_recovery = ((10 - last_rpe) / 10) * 100
    
    # Weighted average
    recovery_score = (
        time_recovery * 0.3 +
        sleep_recovery * 0.25 +
        stress_recovery * 0.2 +
        soreness_recovery * 0.15 +
        rpe_recovery * 0.1
    )
    
    # Training recommendations
    if recovery_score >= 85:
        readiness = "Excellent"
        recommended_rpe = 9.0
        recommendations = ["Go for a PR attempt", "High intensity training ready"]
    elif recovery_score >= 70:
        readiness = "Good"
        recommended_rpe = 7.5
        recommendations = ["Normal training intensity", "Focus on technique"]
    elif recovery_score >= 50:
        readiness = "Moderate"
        recommended_rpe = 6.0
        recommendations = ["Light to moderate training", "Extra warm-up needed"]
    else:
        readiness = "Poor"
        recommended_rpe = 4.0
        recommendations = ["Rest day recommended", "Light mobility work only"]
    
    return {
        "recovery_score": round(recovery_score, 1),
        "recommended_intensity": recommended_rpe,
        "training_readiness": readiness,
        "recommendations": recommendations
    }

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "ML Fitness Tools API - Week 3",
        "version": "1.0.0",
        "endpoints": {
            "/calculate-rpe": "POST - Calculate RPE-based metrics",
            "/predict-strength": "POST - Predict next workout strength",
            "/recovery-status": "POST - Calculate recovery score",
            "/health": "GET - API health check",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0.0"
    }

@app.post("/calculate-rpe", response_model=RPEResponse)
async def calculate_rpe(request: RPERequest):
    """Calculate RPE-based training metrics"""
    try:
        metrics = calculate_rpe_metrics(request.weight, request.reps, request.rpe)
        
        # Generate recommendation
        if request.rpe >= 9:
            recommendation = "High intensity - consider deload next session"
        elif request.rpe >= 7:
            recommendation = "Good training intensity - maintain or slight increase"
        else:
            recommendation = "Conservative load - room for intensity increase"
        
        return RPEResponse(
            adjusted_volume=metrics["adjusted_volume"],
            training_stress=metrics["training_stress"],
            recommendation=recommendation,
            rpe_efficiency=metrics["rpe_efficiency"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict-strength", response_model=StrengthResponse)
async def predict_strength(request: StrengthRequest):
    """Predict next workout strength"""
    try:
        prediction = predict_next_strength(request.recent_sessions, request.target_reps)
        
        next_workout = {
            "recommended_weight": prediction["predicted_weight"],
            "target_reps": request.target_reps,
            "suggested_rpe": 8.0,
            "exercise": request.exercise
        }
        
        # Progression recommendation
        if prediction["trend"] == "increasing":
            progression = "Continue current progression"
        else:
            progression = "Consider technique focus or deload"
        
        return StrengthResponse(
            predicted_weight=prediction["predicted_weight"],
            confidence=prediction["confidence"],
            next_workout=next_workout,
            progression=progression
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/recovery-status", response_model=RecoveryResponse)
async def recovery_status(request: RecoveryRequest):
    """Calculate recovery status and training readiness"""
    try:
        recovery = calculate_recovery_score(
            request.last_session_rpe,
            request.hours_since_training,
            request.sleep_quality,
            request.stress_level,
            request.muscle_soreness
        )
        
        return RecoveryResponse(
            recovery_score=recovery["recovery_score"],
            recommended_intensity=recovery["recommended_intensity"],
            training_readiness=recovery["training_readiness"],
            recommendations=recovery["recommendations"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("🏋️‍♂️ Starting ML Fitness Tools API...")
    print("📊 Week 3: Recovery API")
    print("🌐 API will be available at: http://localhost:8000")
    print("📖 Documentation at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)