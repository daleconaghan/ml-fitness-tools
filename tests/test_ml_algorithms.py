"""Tests for ML algorithms (RPE, strength prediction, recovery, overtraining)"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import recovery_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from recovery_api import (
    calculate_rpe_metrics,
    predict_next_strength,
    calculate_recovery_score,
    detect_overtraining_risk,
    generate_workout_plan
)


class TestRPECalculator:
    """Tests for RPE calculation algorithm"""

    def test_basic_rpe_calculation(self):
        """Test basic RPE metrics calculation"""
        result = calculate_rpe_metrics(weight=100, reps=5, rpe=8.0)

        assert "adjusted_volume" in result
        assert "training_stress" in result
        assert "rpe_efficiency" in result
        assert "estimated_1rm" in result

        # Basic sanity checks
        assert result["adjusted_volume"] > 0
        assert result["training_stress"] > 0
        assert 0 <= result["rpe_efficiency"] <= 1
        assert result["estimated_1rm"] > 100  # Should be higher than working weight

    def test_rpe_high_intensity(self):
        """Test RPE calculation at high intensity"""
        result = calculate_rpe_metrics(weight=100, reps=5, rpe=9.5)

        # At RPE 9.5, estimated 1RM should be very close to working weight
        assert result["estimated_1rm"] < 105  # Should be close to 100
        assert result["rpe_efficiency"] < 0.1  # Low efficiency at high RPE

    def test_rpe_low_intensity(self):
        """Test RPE calculation at low intensity"""
        result = calculate_rpe_metrics(weight=100, reps=5, rpe=6.0)

        # At RPE 6, estimated 1RM should be much higher
        assert result["estimated_1rm"] > 130
        assert result["rpe_efficiency"] > 0.3  # Higher efficiency at lower RPE

    def test_rpe_different_weights(self):
        """Test that heavier weights produce higher volume metrics"""
        light = calculate_rpe_metrics(weight=50, reps=5, rpe=8.0)
        heavy = calculate_rpe_metrics(weight=100, reps=5, rpe=8.0)

        assert heavy["adjusted_volume"] > light["adjusted_volume"]
        assert heavy["training_stress"] > light["training_stress"]


class TestStrengthPredictor:
    """Tests for strength prediction algorithm"""

    def test_basic_prediction(self):
        """Test basic strength prediction"""
        sessions = [
            {"weight": 100, "reps": 5},
            {"weight": 102.5, "reps": 5},
            {"weight": 105, "reps": 5},
        ]

        result = predict_next_strength(sessions, target_reps=5)

        assert "predicted_weight" in result
        assert "confidence" in result
        assert "trend" in result

        # Should predict higher weight based on progression
        assert result["predicted_weight"] > 105
        assert result["trend"] == "increasing"

    def test_prediction_with_insufficient_data(self):
        """Test prediction with only one session"""
        sessions = [{"weight": 100, "reps": 5}]

        result = predict_next_strength(sessions, target_reps=5)

        # Should still return a prediction with lower confidence
        assert result["predicted_weight"] > 0
        assert result["confidence"] == 50.0

    def test_prediction_stable_trend(self):
        """Test prediction with stable weights"""
        sessions = [
            {"weight": 100, "reps": 5},
            {"weight": 100, "reps": 5},
            {"weight": 100, "reps": 5},
        ]

        result = predict_next_strength(sessions, target_reps=5)

        assert result["trend"] == "stable"
        # Prediction should be close to current weight
        assert 98 <= result["predicted_weight"] <= 102

    def test_prediction_empty_sessions(self):
        """Test that empty sessions raise an error"""
        with pytest.raises(ValueError):
            predict_next_strength([], target_reps=5)


class TestRecoveryCalculator:
    """Tests for recovery score calculation"""

    def test_excellent_recovery(self):
        """Test recovery calculation with excellent conditions"""
        result = calculate_recovery_score(
            last_rpe=7.0,
            hours_since=48,
            sleep=9.0,
            stress=2.0,
            soreness=1.0
        )

        assert result["recovery_score"] >= 85
        assert result["training_readiness"] == "Excellent"
        assert result["recommended_intensity"] == 9.0

    def test_poor_recovery(self):
        """Test recovery calculation with poor conditions"""
        result = calculate_recovery_score(
            last_rpe=9.5,
            hours_since=12,
            sleep=4.0,
            stress=9.0,
            soreness=8.0
        )

        assert result["recovery_score"] < 50
        assert result["training_readiness"] == "Poor"
        assert result["recommended_intensity"] <= 5.0
        assert len(result["recommendations"]) > 0

    def test_moderate_recovery(self):
        """Test recovery calculation with moderate conditions"""
        result = calculate_recovery_score(
            last_rpe=8.0,
            hours_since=24,
            sleep=6.5,
            stress=5.0,
            soreness=4.0
        )

        assert 50 <= result["recovery_score"] < 85
        assert result["training_readiness"] in ["Moderate", "Good"]

    def test_recovery_time_factor(self):
        """Test that more time increases recovery score"""
        recent = calculate_recovery_score(
            last_rpe=8.0, hours_since=12, sleep=7.0, stress=5.0, soreness=5.0
        )
        rested = calculate_recovery_score(
            last_rpe=8.0, hours_since=72, sleep=7.0, stress=5.0, soreness=5.0
        )

        assert rested["recovery_score"] > recent["recovery_score"]


class TestOvertrainingDetector:
    """Tests for overtraining risk detection"""

    def test_healthy_training(self):
        """Test detection with healthy training pattern"""
        sessions = [
            {"weight": 100, "reps": 5, "rpe": 7.5},
            {"weight": 102.5, "reps": 5, "rpe": 8.0},
            {"weight": 105, "reps": 5, "rpe": 8.0},
            {"weight": 107.5, "reps": 5, "rpe": 8.5},
            {"weight": 110, "reps": 5, "rpe": 8.0},
        ]

        result = detect_overtraining_risk(
            sessions=sessions,
            sleep_avg=8.0,
            stress_avg=4.0,
            motivation=8.0,
            hr_trend=0
        )

        assert result["risk_level"] == "Low"
        assert result["risk_percentage"] < 25
        assert result["deload_suggested"] == False

    def test_overtraining_pattern(self):
        """Test detection with clear overtraining signs"""
        sessions = [
            {"weight": 120, "reps": 5, "rpe": 8.5},
            {"weight": 122.5, "reps": 5, "rpe": 9.0},
            {"weight": 120, "reps": 4, "rpe": 9.5},
            {"weight": 117.5, "reps": 4, "rpe": 9.5},
            {"weight": 115, "reps": 3, "rpe": 9.0},
            {"weight": 112.5, "reps": 4, "rpe": 9.0},
            {"weight": 110, "reps": 5, "rpe": 8.5},
        ]

        result = detect_overtraining_risk(
            sessions=sessions,
            sleep_avg=5.0,
            stress_avg=8.0,
            motivation=3.0,
            hr_trend=7
        )

        # Should detect high or critical risk
        assert result["risk_level"] in ["High", "Critical"]
        assert result["risk_percentage"] >= 50
        assert result["deload_suggested"] == True
        assert len(result["warning_signs"]) > 0

    def test_insufficient_data(self):
        """Test that insufficient data returns Unknown risk"""
        sessions = [
            {"weight": 100, "reps": 5, "rpe": 8.0},
            {"weight": 102.5, "reps": 5, "rpe": 8.0},
        ]

        result = detect_overtraining_risk(
            sessions=sessions,
            sleep_avg=7.0,
            stress_avg=5.0,
            motivation=7.0
        )

        assert result["risk_level"] == "Unknown"
        assert "Insufficient training data" in result["warning_signs"]

    def test_poor_sleep_increases_risk(self):
        """Test that poor sleep increases overtraining risk"""
        sessions = [
            {"weight": 100 + i*2.5, "reps": 5, "rpe": 8.0}
            for i in range(7)
        ]

        good_sleep = detect_overtraining_risk(
            sessions=sessions, sleep_avg=8.5, stress_avg=4.0, motivation=8.0
        )
        poor_sleep = detect_overtraining_risk(
            sessions=sessions, sleep_avg=5.0, stress_avg=4.0, motivation=8.0
        )

        assert poor_sleep["risk_percentage"] > good_sleep["risk_percentage"]

    def test_invalid_sessions_filtered(self):
        """Test that invalid sessions are properly filtered"""
        sessions = [
            {"weight": 100, "reps": 5, "rpe": 8.0},
            {"weight": 102.5, "reps": 5, "rpe": 8.0},
            None,  # Invalid session
            {"invalid": "data"},  # Missing required fields
            {"weight": 105, "reps": 5, "rpe": 8.0},
        ]

        # Should handle invalid data gracefully
        result = detect_overtraining_risk(
            sessions=sessions,
            sleep_avg=7.0,
            stress_avg=5.0,
            motivation=7.0
        )

        # Should return Unknown due to insufficient valid data (only 3 valid sessions)
        assert result["risk_level"] == "Unknown"


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_zero_weight(self):
        """Test RPE calculation with zero weight"""
        result = calculate_rpe_metrics(weight=0, reps=5, rpe=8.0)
        assert result["adjusted_volume"] == 0
        assert result["training_stress"] == 0

    def test_extreme_rpe_values(self):
        """Test RPE calculation with RPE values not in lookup table"""
        result = calculate_rpe_metrics(weight=100, reps=5, rpe=5.0)
        # Should use default value of 70%
        assert result["estimated_1rm"] > 0

    def test_negative_recovery_hours(self):
        """Test recovery with zero hours since training"""
        result = calculate_recovery_score(
            last_rpe=8.0, hours_since=0, sleep=7.0, stress=5.0, soreness=5.0
        )
        assert result["recovery_score"] >= 0
        assert result["recovery_score"] <= 100


class TestWorkoutPlanGenerator:
    """Tests for workout plan generation (Week 5)"""

    def test_basic_workout_plan_generation(self):
        """Test basic workout plan generation"""
        training_history = {
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
        }

        result = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=4,
            recovery_score=80.0
        )

        assert "weekly_plan" in result
        assert "total_weekly_volume" in result
        assert "estimated_training_stress" in result
        assert "progression_strategy" in result
        assert "recommendations" in result

        # Should have 4 training days + 3 rest days = 7 total days
        assert len(result["weekly_plan"]) == 7

        # Should have some training days with exercises
        training_days_count = sum(1 for day in result["weekly_plan"] if day["exercises"])
        assert training_days_count == 4

        # Volume and stress should be positive
        assert result["total_weekly_volume"] > 0
        assert result["estimated_training_stress"] > 0

    def test_strength_goal_workout_plan(self):
        """Test workout plan generation with strength goal"""
        training_history = {
            "squat": [
                {"weight": 120, "reps": 5, "rpe": 8.5},
                {"weight": 122.5, "reps": 5, "rpe": 8.5},
                {"weight": 125, "reps": 5, "rpe": 9.0},
            ]
        }

        result = generate_workout_plan(
            training_history=training_history,
            goal="strength",
            training_days=3
        )

        assert result["progression_strategy"].lower().find("linear") != -1
        # Strength goal should have higher target weights
        assert result["total_weekly_volume"] > 0

    def test_maintenance_goal_workout_plan(self):
        """Test workout plan generation with maintenance goal"""
        training_history = {
            "squat": [
                {"weight": 100, "reps": 5, "rpe": 7.5},
                {"weight": 100, "reps": 5, "rpe": 7.5},
                {"weight": 100, "reps": 5, "rpe": 7.5},
            ]
        }

        result = generate_workout_plan(
            training_history=training_history,
            goal="maintenance",
            training_days=3
        )

        assert "maintenance" in result["progression_strategy"].lower()

    def test_workout_plan_with_low_recovery(self):
        """Test that low recovery score reduces intensity"""
        training_history = {
            "bench_press": [
                {"weight": 80, "reps": 5, "rpe": 8.0},
                {"weight": 82.5, "reps": 5, "rpe": 8.0},
                {"weight": 85, "reps": 5, "rpe": 8.0},
            ]
        }

        high_recovery = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=3,
            recovery_score=90.0
        )

        low_recovery = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=3,
            recovery_score=40.0
        )

        # Low recovery should result in lower training stress
        assert low_recovery["estimated_training_stress"] < high_recovery["estimated_training_stress"]

        # Low recovery should have recommendations about it
        recommendations_text = " ".join(low_recovery["recommendations"]).lower()
        assert "recovery" in recommendations_text or "sleep" in recommendations_text

    def test_workout_plan_training_split(self):
        """Test that appropriate training splits are used"""
        training_history = {
            "squat": [{"weight": 100, "reps": 5, "rpe": 8.0}] * 3,
            "bench_press": [{"weight": 80, "reps": 5, "rpe": 8.0}] * 3,
            "deadlift": [{"weight": 140, "reps": 5, "rpe": 8.5}] * 3,
        }

        # Test 3-day split (should be Push/Pull/Legs)
        result_3day = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=3
        )
        assert len([d for d in result_3day["weekly_plan"] if d["exercises"]]) == 3

        # Test 4-day split (should be Upper/Lower split)
        result_4day = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=4
        )
        assert len([d for d in result_4day["weekly_plan"] if d["exercises"]]) == 4

    def test_insufficient_training_data(self):
        """Test that insufficient data raises appropriate error"""
        training_history = {}

        with pytest.raises(ValueError, match="No training history"):
            generate_workout_plan(
                training_history=training_history,
                goal="hypertrophy",
                training_days=4
            )

    def test_minimal_training_data(self):
        """Test with minimal but valid training data"""
        training_history = {
            "squat": [
                {"weight": 100, "reps": 5, "rpe": 8.0},
                {"weight": 100, "reps": 5, "rpe": 8.0},
            ]
        }

        # Should work with minimal data
        result = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=2
        )

        assert "weekly_plan" in result
        assert len(result["weekly_plan"]) == 7  # 2 training + 5 rest days

    def test_progression_applied(self):
        """Test that progressive overload is applied"""
        training_history = {
            "squat": [
                {"weight": 100, "reps": 5, "rpe": 8.0},
                {"weight": 102.5, "reps": 5, "rpe": 8.0},
                {"weight": 105, "reps": 5, "rpe": 8.0},
                {"weight": 107.5, "reps": 5, "rpe": 8.0},
            ]
        }

        result = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=3
        )

        # Find a training day with squat
        squat_exercise = None
        for day in result["weekly_plan"]:
            for ex in day["exercises"]:
                if "squat" in ex["exercise"].lower():
                    squat_exercise = ex
                    break
            if squat_exercise:
                break

        # Target weight should be higher than recent average (105)
        if squat_exercise:
            assert squat_exercise["weight_kg"] > 105

    def test_recommendations_generated(self):
        """Test that useful recommendations are generated"""
        training_history = {
            "squat": [
                {"weight": 100, "reps": 5, "rpe": 9.0},
                {"weight": 100, "reps": 5, "rpe": 9.5},
                {"weight": 100, "reps": 5, "rpe": 9.5},
            ]
        }

        result = generate_workout_plan(
            training_history=training_history,
            goal="hypertrophy",
            training_days=3
        )

        # Should recommend deload due to high RPE
        recommendations_text = " ".join(result["recommendations"]).lower()
        assert "rpe" in recommendations_text or "deload" in recommendations_text
