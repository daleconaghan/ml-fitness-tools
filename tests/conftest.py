"""Pytest configuration and fixtures"""

import pytest


@pytest.fixture(scope="session")
def sample_training_sessions():
    """Fixture providing sample training session data"""
    return [
        {"weight": 100, "reps": 5, "rpe": 7.5},
        {"weight": 102.5, "reps": 5, "rpe": 8.0},
        {"weight": 105, "reps": 5, "rpe": 8.0},
        {"weight": 107.5, "reps": 5, "rpe": 8.5},
        {"weight": 110, "reps": 5, "rpe": 8.0},
    ]


@pytest.fixture(scope="session")
def overtraining_sessions():
    """Fixture providing overtraining pattern data"""
    return [
        {"weight": 120, "reps": 5, "rpe": 8.5},
        {"weight": 122.5, "reps": 5, "rpe": 9.0},
        {"weight": 120, "reps": 4, "rpe": 9.5},
        {"weight": 117.5, "reps": 4, "rpe": 9.5},
        {"weight": 115, "reps": 3, "rpe": 9.0},
        {"weight": 112.5, "reps": 4, "rpe": 9.0},
        {"weight": 110, "reps": 5, "rpe": 8.5},
    ]
