"""
RPE-Adjusted Training Volume Calculator
Week 1/260 of ML Fitness Tools
Author: Dale Conaghan
"""

def calculate_effective_volume(sets, reps, weight, rpe):
    """Calculate training volume adjusted for RPE (Rate of Perceived Exertion)"""
    reps_in_reserve = 10 - rpe
    intensity_multiplier = 1 + (rpe - 6) * 0.15 if rpe > 6 else 1.0
    effective_volume = sets * reps * weight * intensity_multiplier
    
    return {
        'raw_volume': sets * reps * weight,
        'effective_volume': round(effective_volume, 1),
        'intensity_multiplier': intensity_multiplier,
        'estimated_reps_in_reserve': reps_in_reserve
    }

def estimate_1rm_from_rpe(weight, reps, rpe):
    """Estimate 1RM from any set using RPE"""
    reps_in_reserve = 10 - rpe
    total_reps_possible = reps + reps_in_reserve
    estimated_1rm = weight * (1 + total_reps_possible / 30)
    return round(estimated_1rm, 1)

if __name__ == "__main__":
    # Example workout
    result = calculate_effective_volume(3, 5, 80, 8)
    print("🏋️ RPE CALCULATOR - Week 1/260")
    print("=" * 40)
    print(f"Raw Volume: {result['raw_volume']}kg")
    print(f"Effective Volume: {result['effective_volume']}kg")
    print(f"Intensity Multiplier: {result['intensity_multiplier']}x")
