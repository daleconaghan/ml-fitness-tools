"""Tests for FastAPI endpoints"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path to import recovery_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from recovery_api import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "/calculate-rpe" in data["endpoints"]

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "api_version" in data


class TestRPEEndpoint:
    """Tests for /calculate-rpe endpoint"""

    def test_valid_rpe_request(self):
        """Test valid RPE calculation request"""
        payload = {
            "weight": 100.0,
            "reps": 5,
            "rpe": 8.0,
            "exercise": "squat"
        }

        response = client.post("/calculate-rpe", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "adjusted_volume" in data
        assert "training_stress" in data
        assert "recommendation" in data
        assert "rpe_efficiency" in data

        assert data["adjusted_volume"] > 0
        assert data["training_stress"] > 0

    def test_rpe_without_exercise(self):
        """Test RPE calculation with default exercise"""
        payload = {
            "weight": 100.0,
            "reps": 5,
            "rpe": 8.0
        }

        response = client.post("/calculate-rpe", json=payload)
        assert response.status_code == 200

    def test_rpe_high_intensity(self):
        """Test RPE calculation returns deload recommendation at high RPE"""
        payload = {
            "weight": 100.0,
            "reps": 5,
            "rpe": 9.5,
            "exercise": "bench_press"
        }

        response = client.post("/calculate-rpe", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "deload" in data["recommendation"].lower()

    def test_rpe_missing_fields(self):
        """Test RPE calculation with missing required fields"""
        payload = {
            "weight": 100.0,
            "reps": 5
            # Missing rpe
        }

        response = client.post("/calculate-rpe", json=payload)
        assert response.status_code == 422  # Validation error

    def test_rpe_invalid_types(self):
        """Test RPE calculation with invalid data types"""
        payload = {
            "weight": "not_a_number",
            "reps": 5,
            "rpe": 8.0
        }

        response = client.post("/calculate-rpe", json=payload)
        assert response.status_code == 422


class TestStrengthPredictionEndpoint:
    """Tests for /predict-strength endpoint"""

    def test_valid_strength_prediction(self):
        """Test valid strength prediction request"""
        payload = {
            "recent_sessions": [
                {"weight": 100, "reps": 5},
                {"weight": 102.5, "reps": 5},
                {"weight": 105, "reps": 5}
            ],
            "target_reps": 5,
            "exercise": "squat"
        }

        response = client.post("/predict-strength", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "predicted_weight" in data
        assert "confidence" in data
        assert "next_workout" in data
        assert "progression" in data

        assert data["predicted_weight"] > 0
        assert 0 <= data["confidence"] <= 100

    def test_strength_prediction_with_defaults(self):
        """Test strength prediction with default values"""
        payload = {
            "recent_sessions": [
                {"weight": 100, "reps": 5},
                {"weight": 102.5, "reps": 5}
            ]
        }

        response = client.post("/predict-strength", json=payload)
        assert response.status_code == 200

    def test_strength_prediction_empty_sessions(self):
        """Test strength prediction with empty sessions"""
        payload = {
            "recent_sessions": [],
            "target_reps": 5
        }

        response = client.post("/predict-strength", json=payload)
        assert response.status_code == 400  # Bad request

    def test_strength_prediction_invalid_data(self):
        """Test strength prediction with invalid session data"""
        payload = {
            "recent_sessions": "not_a_list",
            "target_reps": 5
        }

        response = client.post("/predict-strength", json=payload)
        assert response.status_code == 422


class TestRecoveryEndpoint:
    """Tests for /recovery-status endpoint"""

    def test_valid_recovery_request(self):
        """Test valid recovery status request"""
        payload = {
            "last_session_rpe": 8.5,
            "hours_since_training": 36,
            "sleep_quality": 7.0,
            "stress_level": 4.0,
            "muscle_soreness": 3.0
        }

        response = client.post("/recovery-status", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "recovery_score" in data
        assert "recommended_intensity" in data
        assert "training_readiness" in data
        assert "recommendations" in data

        assert 0 <= data["recovery_score"] <= 100
        assert data["training_readiness"] in ["Excellent", "Good", "Moderate", "Poor"]
        assert len(data["recommendations"]) > 0

    def test_recovery_excellent_conditions(self):
        """Test recovery with excellent conditions"""
        payload = {
            "last_session_rpe": 7.0,
            "hours_since_training": 48,
            "sleep_quality": 9.0,
            "stress_level": 2.0,
            "muscle_soreness": 1.0
        }

        response = client.post("/recovery-status", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["training_readiness"] == "Excellent"
        assert data["recovery_score"] >= 85

    def test_recovery_poor_conditions(self):
        """Test recovery with poor conditions"""
        payload = {
            "last_session_rpe": 9.5,
            "hours_since_training": 12,
            "sleep_quality": 4.0,
            "stress_level": 9.0,
            "muscle_soreness": 8.0
        }

        response = client.post("/recovery-status", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["training_readiness"] == "Poor"
        assert data["recovery_score"] < 50

    def test_recovery_missing_fields(self):
        """Test recovery request with missing fields"""
        payload = {
            "last_session_rpe": 8.5,
            "hours_since_training": 36
            # Missing other required fields
        }

        response = client.post("/recovery-status", json=payload)
        assert response.status_code == 422


class TestOvertrainingEndpoint:
    """Tests for /overtraining-risk endpoint"""

    def test_valid_overtraining_request(self):
        """Test valid overtraining risk request"""
        payload = {
            "recent_sessions": [
                {"weight": 100 + i*2.5, "reps": 5, "rpe": 8.0}
                for i in range(7)
            ],
            "sleep_quality_avg": 7.0,
            "stress_level_avg": 5.0,
            "motivation_level": 7.0,
            "resting_hr_trend": 2.0
        }

        response = client.post("/overtraining-risk", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "risk_level" in data
        assert "risk_percentage" in data
        assert "warning_signs" in data
        assert "recommendations" in data
        assert "deload_suggested" in data

        assert data["risk_level"] in ["Low", "Moderate", "High", "Critical", "Unknown"]
        assert 0 <= data["risk_percentage"] <= 100
        assert isinstance(data["deload_suggested"], bool)

    def test_overtraining_healthy_pattern(self):
        """Test overtraining detection with healthy training"""
        payload = {
            "recent_sessions": [
                {"weight": 100, "reps": 5, "rpe": 7.5},
                {"weight": 102.5, "reps": 5, "rpe": 8.0},
                {"weight": 105, "reps": 5, "rpe": 8.0},
                {"weight": 107.5, "reps": 5, "rpe": 8.5},
                {"weight": 110, "reps": 5, "rpe": 8.0},
            ],
            "sleep_quality_avg": 8.0,
            "stress_level_avg": 4.0,
            "motivation_level": 8.0
        }

        response = client.post("/overtraining-risk", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_level"] == "Low"
        assert data["deload_suggested"] == False

    def test_overtraining_high_risk_pattern(self):
        """Test overtraining detection with concerning pattern"""
        payload = {
            "recent_sessions": [
                {"weight": 120, "reps": 5, "rpe": 8.5},
                {"weight": 122.5, "reps": 5, "rpe": 9.0},
                {"weight": 120, "reps": 4, "rpe": 9.5},
                {"weight": 117.5, "reps": 4, "rpe": 9.5},
                {"weight": 115, "reps": 3, "rpe": 9.0},
                {"weight": 112.5, "reps": 4, "rpe": 9.0},
                {"weight": 110, "reps": 5, "rpe": 8.5},
            ],
            "sleep_quality_avg": 5.0,
            "stress_level_avg": 8.0,
            "motivation_level": 3.0,
            "resting_hr_trend": 7.0
        }

        response = client.post("/overtraining-risk", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_level"] in ["High", "Critical"]
        assert data["deload_suggested"] == True
        assert len(data["warning_signs"]) > 0

    def test_overtraining_without_hr_trend(self):
        """Test overtraining request without optional HR trend"""
        payload = {
            "recent_sessions": [
                {"weight": 100 + i*2.5, "reps": 5, "rpe": 8.0}
                for i in range(6)
            ],
            "sleep_quality_avg": 7.0,
            "stress_level_avg": 5.0,
            "motivation_level": 7.0
        }

        response = client.post("/overtraining-risk", json=payload)
        assert response.status_code == 200

    def test_overtraining_insufficient_data(self):
        """Test overtraining with insufficient session data"""
        payload = {
            "recent_sessions": [
                {"weight": 100, "reps": 5, "rpe": 8.0},
                {"weight": 102.5, "reps": 5, "rpe": 8.0}
            ],
            "sleep_quality_avg": 7.0,
            "stress_level_avg": 5.0,
            "motivation_level": 7.0
        }

        response = client.post("/overtraining-risk", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_level"] == "Unknown"


class TestCORS:
    """Tests for CORS configuration"""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = client.get("/health")
        assert response.status_code == 200

        # CORS headers should be set by middleware
        # Note: TestClient may not include all CORS headers
        # This is more of a smoke test


class TestDocumentation:
    """Tests for API documentation endpoints"""

    def test_openapi_schema(self):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Verify key endpoints are documented
        assert "/calculate-rpe" in schema["paths"]
        assert "/predict-strength" in schema["paths"]
        assert "/recovery-status" in schema["paths"]
        assert "/overtraining-risk" in schema["paths"]
        assert "/generate-workout-plan" in schema["paths"]


class TestWorkoutPlanEndpoint:
    """Tests for /generate-workout-plan endpoint (Week 5)"""

    def test_valid_workout_plan_request(self):
        """Test valid workout plan generation request"""
        payload = {
            "training_history": {
                "squat": [
                    {"weight": 100, "reps": 5, "rpe": 8.0},
                    {"weight": 102.5, "reps": 5, "rpe": 8.0},
                    {"weight": 105, "reps": 5, "rpe": 8.5},
                ],
                "bench_press": [
                    {"weight": 80, "reps": 5, "rpe": 7.5},
                    {"weight": 82.5, "reps": 5, "rpe": 8.0},
                    {"weight": 85, "reps": 5, "rpe": 8.0},
                ]
            },
            "goal": "hypertrophy",
            "training_days_per_week": 4,
            "recovery_score": 80.0
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "weekly_plan" in data
        assert "total_weekly_volume" in data
        assert "estimated_training_stress" in data
        assert "progression_strategy" in data
        assert "recommendations" in data

        # Should have 7 days total
        assert len(data["weekly_plan"]) == 7

        # Each day should have required fields
        for day in data["weekly_plan"]:
            assert "day" in day
            assert "exercises" in day
            assert "notes" in day

        # Volume and stress should be positive
        assert data["total_weekly_volume"] > 0
        assert data["estimated_training_stress"] > 0

    def test_workout_plan_with_strength_goal(self):
        """Test workout plan with strength goal"""
        payload = {
            "training_history": {
                "squat": [
                    {"weight": 120, "reps": 5, "rpe": 8.5},
                    {"weight": 122.5, "reps": 5, "rpe": 8.5},
                    {"weight": 125, "reps": 5, "rpe": 9.0},
                ]
            },
            "goal": "strength",
            "training_days_per_week": 3
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "linear" in data["progression_strategy"].lower()

    def test_workout_plan_with_maintenance_goal(self):
        """Test workout plan with maintenance goal"""
        payload = {
            "training_history": {
                "squat": [
                    {"weight": 100, "reps": 5, "rpe": 7.5},
                    {"weight": 100, "reps": 5, "rpe": 7.5},
                    {"weight": 100, "reps": 5, "rpe": 7.5},
                ]
            },
            "goal": "maintenance",
            "training_days_per_week": 3
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "maintenance" in data["progression_strategy"].lower()

    def test_workout_plan_default_values(self):
        """Test workout plan with default values"""
        payload = {
            "training_history": {
                "bench_press": [
                    {"weight": 80, "reps": 5, "rpe": 8.0},
                    {"weight": 82.5, "reps": 5, "rpe": 8.0},
                    {"weight": 85, "reps": 5, "rpe": 8.0},
                ]
            }
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Should use default goal (hypertrophy) and training_days (4)
        # Plan should have at least some days
        assert len(data["weekly_plan"]) > 0
        assert data["total_weekly_volume"] > 0

    def test_workout_plan_with_low_recovery(self):
        """Test workout plan adjusts for low recovery"""
        payload = {
            "training_history": {
                "squat": [
                    {"weight": 100, "reps": 5, "rpe": 8.0},
                    {"weight": 102.5, "reps": 5, "rpe": 8.0},
                    {"weight": 105, "reps": 5, "rpe": 8.0},
                ]
            },
            "goal": "hypertrophy",
            "training_days_per_week": 4,
            "recovery_score": 40.0
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Should have recommendations about recovery
        recommendations_text = " ".join(data["recommendations"]).lower()
        assert "recovery" in recommendations_text or "sleep" in recommendations_text

    def test_workout_plan_empty_history(self):
        """Test workout plan with empty training history"""
        payload = {
            "training_history": {},
            "goal": "hypertrophy",
            "training_days_per_week": 4
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 400

    def test_workout_plan_missing_fields(self):
        """Test workout plan with missing required fields"""
        payload = {
            # Missing training_history
            "goal": "hypertrophy",
            "training_days_per_week": 4
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 422  # Validation error

    def test_workout_plan_invalid_goal(self):
        """Test workout plan with invalid goal"""
        payload = {
            "training_history": {
                "squat": [
                    {"weight": 100, "reps": 5, "rpe": 8.0},
                    {"weight": 102.5, "reps": 5, "rpe": 8.0},
                ]
            },
            "goal": "invalid_goal",  # Invalid
            "training_days_per_week": 4
        }

        # Should still work - goal is validated within function logic
        response = client.post("/generate-workout-plan", json=payload)
        # Either succeeds with default handling or returns error
        assert response.status_code in [200, 400]

    def test_workout_plan_different_training_days(self):
        """Test workout plan with different training days per week"""
        training_history = {
            "squat": [{"weight": 100, "reps": 5, "rpe": 8.0}] * 3,
            "bench_press": [{"weight": 80, "reps": 5, "rpe": 8.0}] * 3,
            "deadlift": [{"weight": 140, "reps": 5, "rpe": 8.5}] * 3,
        }

        for days in [2, 3, 4, 5]:
            payload = {
                "training_history": training_history,
                "goal": "hypertrophy",
                "training_days_per_week": days
            }

            response = client.post("/generate-workout-plan", json=payload)
            assert response.status_code == 200

            data = response.json()
            # Should have at least some training days (may be less than requested if exercises don't match all splits)
            training_days = [d for d in data["weekly_plan"] if d["exercises"]]
            assert len(training_days) > 0
            assert len(training_days) <= days

    def test_workout_plan_exercise_selection(self):
        """Test that exercises are appropriately selected for workout days"""
        payload = {
            "training_history": {
                "squat": [{"weight": 100, "reps": 5, "rpe": 8.0}] * 3,
                "bench_press": [{"weight": 80, "reps": 5, "rpe": 8.0}] * 3,
                "deadlift": [{"weight": 140, "reps": 5, "rpe": 8.5}] * 3,
            },
            "goal": "hypertrophy",
            "training_days_per_week": 3
        }

        response = client.post("/generate-workout-plan", json=payload)
        assert response.status_code == 200

        data = response.json()

        # All exercises should appear in the plan
        all_exercises = []
        for day in data["weekly_plan"]:
            for ex in day["exercises"]:
                all_exercises.append(ex["exercise"].lower())

        # Check that our exercises are included
        assert any("squat" in ex for ex in all_exercises)
        assert any("bench" in ex or "press" in ex for ex in all_exercises)
        assert any("deadlift" in ex for ex in all_exercises)
