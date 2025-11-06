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
import os
from pathlib import Path

# Configuration from environment variables
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
).split(",")

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
TRAINING_DATA_PATH = SCRIPT_DIR / 'training_data.json'

# Load existing models/data
try:
    with open(TRAINING_DATA_PATH, 'r') as f:
        training_data = json.load(f)
except FileNotFoundError:
    raise RuntimeError(f"Training data file not found at {TRAINING_DATA_PATH}. Please ensure training_data.json exists.")
except json.JSONDecodeError as e:
    raise RuntimeError(f"Invalid JSON in training data file: {e}")

app = FastAPI(
    title="ML Fitness Tools API",
    description="API for RPE calculations and strength predictions",
    version="1.0.0"
)

# Enable CORS with secure defaults
# To allow all origins (NOT recommended for production), set ALLOWED_ORIGINS="*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
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

class OvertrainingRequest(BaseModel):
    recent_sessions: List[Dict]  # Last 7-14 training sessions
    sleep_quality_avg: float     # 1-10 scale, last 7 days
    stress_level_avg: float      # 1-10 scale, last 7 days
    motivation_level: float      # 1-10 scale
    resting_hr_trend: Optional[float] = None  # % change from baseline
    
class OvertrainingResponse(BaseModel):
    risk_level: str              # Low/Moderate/High/Critical
    risk_percentage: float       # 0-100%
    warning_signs: List[str]
    recommendations: List[str]
    deload_suggested: bool

class WorkoutPlanRequest(BaseModel):
    training_history: Dict[str, List[Dict]]  # Exercise name -> sessions
    goal: str = "hypertrophy"  # strength, hypertrophy, maintenance
    training_days_per_week: int = 4
    recovery_score: Optional[float] = None  # 0-100, optional

class DailyWorkout(BaseModel):
    day: str
    exercises: List[Dict]  # List of exercises with sets, reps, weight, rpe
    notes: str

class WorkoutPlanResponse(BaseModel):
    weekly_plan: List[DailyWorkout]
    total_weekly_volume: float
    estimated_training_stress: float
    progression_strategy: str
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

# New Overtraining Detection Algorithm (Week 4)
def detect_overtraining_risk(sessions: List[Dict], sleep_avg: float, stress_avg: float, 
                           motivation: float, hr_trend: Optional[float] = None) -> Dict:
    """Detect overtraining risk based on multiple factors"""
    
    # Filter out invalid sessions
    valid_sessions = [s for s in sessions if s and 'weight' in s and 'reps' in s and 'rpe' in s]
    
    if len(valid_sessions) < 5:
        return {
            "risk_level": "Unknown",
            "risk_percentage": 0.0,
            "warning_signs": ["Insufficient training data"],
            "recommendations": ["Track at least 5 training sessions"],
            "deload_suggested": False
        }
    
    warning_signs = []
    risk_factors = []
    
    # 1. Training load analysis
    recent_loads = []
    rpe_trend = []
    
    for session in valid_sessions[-7:]:  # Last week
        weight = session.get('weight', 0)
        reps = session.get('reps', 0)
        rpe = session.get('rpe', 6)
        load = weight * reps * (rpe / 10)  # Weighted load
        recent_loads.append(load)
        rpe_trend.append(rpe)
    
    # Check for declining performance with high RPE
    if len(recent_loads) >= 4:
        early_avg = np.mean(recent_loads[:len(recent_loads)//2])
        late_avg = np.mean(recent_loads[len(recent_loads)//2:])
        rpe_avg = np.mean(rpe_trend[-4:])
        
        if late_avg < early_avg * 0.95 and rpe_avg > 8.5:
            risk_factors.append(25)
            warning_signs.append("Decreasing performance despite high effort")
    
    # 2. RPE inflation check
    if len(rpe_trend) >= 5:
        rpe_recent = np.mean(rpe_trend[-3:])
        rpe_baseline = np.mean(rpe_trend[:-3])
        
        if rpe_recent > rpe_baseline + 0.8:
            risk_factors.append(20)
            warning_signs.append("RPE inflation detected")
    
    # 3. Training frequency/volume check
    total_volume = sum(recent_loads)
    sessions_per_week = len([s for s in valid_sessions[-7:] if s])
    
    if sessions_per_week > 6 and total_volume > np.mean(recent_loads) * 10:
        risk_factors.append(15)
        warning_signs.append("High training frequency and volume")
    
    # 4. Recovery metrics
    if sleep_avg < 6:
        risk_factors.append(20)
        warning_signs.append("Poor sleep quality")
    elif sleep_avg < 7:
        risk_factors.append(10)
        warning_signs.append("Suboptimal sleep quality")
    
    if stress_avg > 7:
        risk_factors.append(15)
        warning_signs.append("High stress levels")
    elif stress_avg > 5:
        risk_factors.append(8)
        warning_signs.append("Elevated stress levels")
    
    # 5. Motivation and psychological markers
    if motivation < 4:
        risk_factors.append(18)
        warning_signs.append("Low training motivation")
    elif motivation < 6:
        risk_factors.append(10)
        warning_signs.append("Decreased training motivation")
    
    # 6. Heart rate trend (if provided)
    if hr_trend and hr_trend > 5:  # 5% increase from baseline
        risk_factors.append(15)
        warning_signs.append("Elevated resting heart rate")
    
    # Calculate total risk
    total_risk = min(100, sum(risk_factors))
    
    # Determine risk level and recommendations
    if total_risk >= 75:
        risk_level = "Critical"
        deload_suggested = True
        recommendations = [
            "Immediate deload recommended",
            "Reduce training volume by 40-50%",
            "Focus on sleep and stress management",
            "Consider taking 3-5 days off training"
        ]
    elif total_risk >= 50:
        risk_level = "High"
        deload_suggested = True
        recommendations = [
            "Planned deload week recommended",
            "Reduce training intensity to RPE 6-7",
            "Increase recovery focus",
            "Monitor symptoms closely"
        ]
    elif total_risk >= 25:
        risk_level = "Moderate"
        deload_suggested = False
        recommendations = [
            "Monitor training load carefully",
            "Ensure adequate sleep (7-9 hours)",
            "Consider reducing volume by 10-20%",
            "Add extra rest day this week"
        ]
    else:
        risk_level = "Low"
        deload_suggested = False
        recommendations = [
            "Training load appears sustainable",
            "Continue current program",
            "Maintain good recovery practices"
        ]
    
    if not warning_signs:
        warning_signs = ["No significant warning signs detected"]
    
    return {
        "risk_level": risk_level,
        "risk_percentage": round(total_risk, 1),
        "warning_signs": warning_signs,
        "recommendations": recommendations,
        "deload_suggested": deload_suggested
    }

# New Workout Plan Recommender (Week 5)
# Exercise-specific progression rates (kg per week)
EXERCISE_PROGRESSION_RATES = {
    'squat': 2.5,
    'deadlift': 2.5,
    'bench_press': 1.25,
    'bench': 1.25,
    'overhead_press': 0.625,
    'press': 0.625,
    'row': 1.25,
    'pull': 0.625,
    'curl': 0.5,
    'lateral': 0.25,
    'tricep': 0.5,
    'default': 1.0
}

# Rep ranges for undulating periodization
DUP_PATTERNS = {
    'strength': [
        {'sets': 5, 'reps': 3, 'intensity': 0.90, 'label': 'Heavy'},
        {'sets': 4, 'reps': 6, 'intensity': 0.85, 'label': 'Medium'},
        {'sets': 3, 'reps': 5, 'intensity': 0.87, 'label': 'Moderate'}
    ],
    'hypertrophy': [
        {'sets': 3, 'reps': 10, 'intensity': 0.70, 'label': 'Volume'},
        {'sets': 4, 'reps': 8, 'intensity': 0.75, 'label': 'Medium'},
        {'sets': 3, 'reps': 12, 'intensity': 0.65, 'label': 'Pump'}
    ],
    'maintenance': [
        {'sets': 3, 'reps': 8, 'intensity': 0.70, 'label': 'Moderate'},
        {'sets': 3, 'reps': 10, 'intensity': 0.65, 'label': 'Light'},
        {'sets': 3, 'reps': 6, 'intensity': 0.75, 'label': 'Medium'}
    ]
}

def get_exercise_progression_rate(exercise_name: str) -> float:
    """Get realistic progression rate for an exercise"""
    exercise_lower = exercise_name.lower()
    for key, rate in EXERCISE_PROGRESSION_RATES.items():
        if key in exercise_lower:
            return rate
    return EXERCISE_PROGRESSION_RATES['default']

def calculate_rpe_cap(recovery_score: Optional[float], avg_recent_rpe: float) -> float:
    """Calculate maximum RPE based on recovery and fatigue"""
    base_cap = 9.5

    # Adjust for recovery score
    if recovery_score is not None:
        if recovery_score < 50:
            base_cap = 7.0
        elif recovery_score < 60:
            base_cap = 7.5
        elif recovery_score < 70:
            base_cap = 8.0
        elif recovery_score < 80:
            base_cap = 8.5

    # Adjust for cumulative fatigue (high recent RPE)
    if avg_recent_rpe > 8.5:
        base_cap = min(base_cap, 8.0)  # Force deload if fatigue is high
    elif avg_recent_rpe > 8.0:
        base_cap = min(base_cap, 8.5)

    return base_cap

def should_deload(avg_recent_rpe: float, recovery_score: Optional[float]) -> bool:
    """Determine if a deload week is needed"""
    # Deload if recent RPE is consistently very high
    if avg_recent_rpe > 8.7:
        return True
    # Deload if recovery is critically low
    if recovery_score is not None and recovery_score < 50:
        return True
    return False

def generate_workout_plan(training_history: Dict[str, List[Dict]], goal: str,
                         training_days: int, recovery_score: Optional[float] = None) -> Dict:
    """Generate weekly workout plan based on training history and goals with realistic progression"""

    if not training_history:
        raise ValueError("No training history provided")

    # Analyze recent training for each exercise
    exercise_analysis = {}
    total_volume = 0
    total_stress = 0

    for exercise, sessions in training_history.items():
        if not sessions:
            continue

        # Get last 4 weeks of data (up to 12 sessions per exercise)
        recent_sessions = sessions[-12:] if len(sessions) > 12 else sessions

        if len(recent_sessions) < 2:
            continue

        # Analyze progression
        weights = [s.get('weight', 0) for s in recent_sessions[-5:]]
        rpes = [s.get('rpe', 8) for s in recent_sessions[-5:]]

        # Calculate average and trend
        avg_weight = np.mean(weights)
        avg_rpe = np.mean(rpes)

        # Get exercise-specific progression rate
        progression_kg = get_exercise_progression_rate(exercise)

        # Calculate percentage progression from absolute kg progression
        progression_rate = progression_kg / avg_weight if avg_weight > 0 else 0.025

        # Estimate 1RM from recent best set
        best_recent = max(recent_sessions[-3:], key=lambda x: x.get('weight', 0))
        rpe_to_percent = {10: 100, 9.5: 97, 9: 94, 8.5: 91, 8: 88, 7.5: 85, 7: 82}
        intensity_percent = rpe_to_percent.get(best_recent.get('rpe', 8), 85)
        estimated_1rm = best_recent.get('weight', avg_weight) / (intensity_percent / 100)

        exercise_analysis[exercise] = {
            'avg_weight': avg_weight,
            'avg_rpe': avg_rpe,
            'progression_rate': progression_rate,
            'progression_kg': progression_kg,
            'estimated_1rm': estimated_1rm,
            'recent_sessions': len(recent_sessions)
        }

    if not exercise_analysis:
        raise ValueError("Insufficient training data to generate plan")

    # Calculate overall fatigue metrics
    avg_recent_rpe = np.mean([analysis['avg_rpe'] for analysis in exercise_analysis.values()])
    rpe_cap = calculate_rpe_cap(recovery_score, avg_recent_rpe)
    is_deload = should_deload(avg_recent_rpe, recovery_score)

    # Determine training split based on days per week
    if training_days <= 2:
        split = ["Full Body A", "Full Body B"]
    elif training_days == 3:
        split = ["Push", "Pull", "Legs"]
    elif training_days == 4:
        split = ["Upper A", "Lower A", "Upper B", "Lower B"]
    elif training_days == 5:
        split = ["Push", "Pull", "Legs", "Upper", "Lower"]
    else:
        split = ["Push", "Pull", "Legs", "Upper", "Lower", "Full Body"]

    # Get DUP pattern for the goal
    dup_pattern = DUP_PATTERNS.get(goal, DUP_PATTERNS['hypertrophy'])

    # Deload adjustments if needed
    deload_volume_mult = 0.5 if is_deload else 1.0
    deload_intensity_mult = 0.85 if is_deload else 1.0

    # Generate weekly plan
    weekly_plan = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i in range(training_days):
        day_type = split[i % len(split)]
        day_name = day_names[i]

        # Select DUP pattern for this day (rotate through patterns)
        dup_day = dup_pattern[i % len(dup_pattern)]

        # Select exercises for this day based on split type
        day_exercises = []

        for exercise_name, analysis in exercise_analysis.items():
            # Simple exercise categorization
            exercise_lower = exercise_name.lower()

            # Determine if exercise fits this day
            include = False
            if "Full Body" in day_type:
                include = True
            elif "Push" in day_type and any(x in exercise_lower for x in ['bench', 'press', 'chest']):
                include = True
            elif "Pull" in day_type and any(x in exercise_lower for x in ['row', 'pull', 'deadlift']):
                include = True
            elif "Legs" in day_type or "Lower" in day_type:
                include = any(x in exercise_lower for x in ['squat', 'leg', 'deadlift'])
            elif "Upper" in day_type:
                include = any(x in exercise_lower for x in ['bench', 'press', 'row', 'pull', 'chest'])

            if include:
                # Calculate target weight using exercise-specific progression
                if is_deload:
                    # Deload: reduce weight significantly
                    target_weight = analysis['avg_weight'] * deload_intensity_mult
                elif goal == "maintenance":
                    # Maintenance: keep weight stable
                    target_weight = analysis['avg_weight']
                else:
                    # Progressive overload: add progression in kg
                    target_weight = analysis['avg_weight'] + analysis['progression_kg']

                # Apply DUP intensity adjustment (percentage of estimated 1RM)
                if not is_deload:
                    target_weight = analysis['estimated_1rm'] * dup_day['intensity']

                # Use DUP sets and reps
                sets = int(dup_day['sets'] * deload_volume_mult)
                sets = max(1, sets)  # At least 1 set
                reps = dup_day['reps']

                # Calculate target RPE with cap
                base_rpe = 7.0 + (dup_day['intensity'] - 0.65) * 10  # Scale RPE with intensity
                target_rpe = min(base_rpe, rpe_cap)

                # Add some descriptive notes
                if is_deload:
                    notes = f"DELOAD - 50% volume, lighter weight"
                else:
                    notes = f"{dup_day['label']} day - {int(dup_day['intensity']*100)}% 1RM"

                day_exercises.append({
                    "exercise": exercise_name,
                    "sets": sets,
                    "reps": reps,
                    "weight_kg": round(target_weight, 1),
                    "target_rpe": round(target_rpe, 1),
                    "notes": notes
                })

                # Calculate volume for this exercise
                volume = target_weight * reps * sets
                total_volume += volume
                total_stress += (volume * target_rpe) / 10

        # Create daily workout
        if day_exercises:
            workout_notes = f"{day_type} workout - {dup_day['label']}"
            if is_deload:
                workout_notes += " [DELOAD WEEK]"
            elif recovery_score and recovery_score < 70:
                workout_notes += " - RPE capped for recovery"

            weekly_plan.append({
                "day": day_name,
                "exercises": day_exercises,
                "notes": workout_notes
            })

    # Add rest days
    rest_days_needed = 7 - training_days
    for i in range(rest_days_needed):
        rest_day_index = training_days + i
        if rest_day_index < 7:
            weekly_plan.append({
                "day": day_names[rest_day_index],
                "exercises": [],
                "notes": "Rest day - Focus on recovery"
            })

    # Generate progression strategy based on current state
    if is_deload:
        progression_strategy = "DELOAD WEEK: Reduce volume by 50%, lighter weights. Focus on recovery and technique refinement"
    elif goal == "strength":
        progression_strategy = "Undulating periodization with exercise-specific progression. Rotate heavy (90%), medium (85%), and moderate (87%) days"
    elif goal == "hypertrophy":
        progression_strategy = "Daily undulating periodization: Volume day (70%), Medium day (75%), Pump day (65%). Progress exercises at realistic rates"
    else:
        progression_strategy = "Maintenance with variety: Rotate intensities to maintain fitness without fatigue accumulation"

    # Generate realistic recommendations
    recommendations = []

    if is_deload:
        recommendations.append("🔴 DELOAD RECOMMENDED: High fatigue detected - reduce volume and intensity this week")
    elif avg_recent_rpe > 8.3:
        recommendations.append("⚠️  Fatigue is accumulating - deload may be needed soon")

    if recovery_score is not None:
        if recovery_score < 60:
            recommendations.append("🛌 Low recovery score - prioritize 8+ hours sleep and stress management")
        elif recovery_score < 75:
            recommendations.append("💤 Moderate recovery - RPE has been capped to prevent overtraining")

    # Exercise-specific progression feedback
    for exercise, analysis in exercise_analysis.items():
        prog_kg = analysis['progression_kg']
        if prog_kg >= 2.5:
            recommendations.append(f"💪 {exercise}: Adding +{prog_kg}kg per week (compound movement)")
        elif prog_kg < 1.0:
            recommendations.append(f"🎯 {exercise}: Small progressions (+{prog_kg}kg) - normal for isolation exercises")

    if len(exercise_analysis) < 3:
        recommendations.append("📊 Consider adding more exercise variety for balanced development")

    recommendations.append(f"📅 Training {training_days} days/week with DUP - different intensities each session")

    return {
        "weekly_plan": weekly_plan,
        "total_weekly_volume": round(total_volume, 1),
        "estimated_training_stress": round(total_stress, 1),
        "progression_strategy": progression_strategy,
        "recommendations": recommendations
    }

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "ML Fitness Tools API - Week 5",
        "version": "1.2.0",
        "endpoints": {
            "/calculate-rpe": "POST - Calculate RPE-based metrics",
            "/predict-strength": "POST - Predict next workout strength",
            "/recovery-status": "POST - Calculate recovery score",
            "/overtraining-risk": "POST - Detect overtraining risk",
            "/generate-workout-plan": "POST - Generate weekly workout plan",
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

@app.post("/overtraining-risk", response_model=OvertrainingResponse)
async def overtraining_risk(request: OvertrainingRequest):
    """Detect overtraining risk based on training data and recovery metrics"""
    try:
        risk_analysis = detect_overtraining_risk(
            request.recent_sessions,
            request.sleep_quality_avg,
            request.stress_level_avg,
            request.motivation_level,
            request.resting_hr_trend
        )
        
        return OvertrainingResponse(
            risk_level=risk_analysis["risk_level"],
            risk_percentage=risk_analysis["risk_percentage"],
            warning_signs=risk_analysis["warning_signs"],
            recommendations=risk_analysis["recommendations"],
            deload_suggested=risk_analysis["deload_suggested"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-workout-plan", response_model=WorkoutPlanResponse)
async def generate_workout_plan_endpoint(request: WorkoutPlanRequest):
    """Generate weekly workout plan based on training history and goals"""
    try:
        plan = generate_workout_plan(
            request.training_history,
            request.goal,
            request.training_days_per_week,
            request.recovery_score
        )

        # Convert plan to response format
        daily_workouts = [
            DailyWorkout(
                day=day_data["day"],
                exercises=day_data["exercises"],
                notes=day_data["notes"]
            )
            for day_data in plan["weekly_plan"]
        ]

        return WorkoutPlanResponse(
            weekly_plan=daily_workouts,
            total_weekly_volume=plan["total_weekly_volume"],
            estimated_training_stress=plan["estimated_training_stress"],
            progression_strategy=plan["progression_strategy"],
            recommendations=plan["recommendations"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    # Configuration from environment variables
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))

    print("🏋️‍♂️ Starting ML Fitness Tools API...")
    print("📊 Week 5: Workout Plan Recommender")
    print("🚨 New feature: /generate-workout-plan endpoint")
    print(f"🌐 API will be available at: http://localhost:{PORT}")
    print(f"📖 Documentation at: http://localhost:{PORT}/docs")
    print(f"🔒 Allowed origins: {', '.join(ALLOWED_ORIGINS)}")

    uvicorn.run(app, host=HOST, port=PORT)