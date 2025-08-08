"""
Week 2/260: Linear Regression for Strength Prediction
Predicts next workout performance based on training history
Author: Dale Conaghan
"""

import json
import numpy as np
from sklearn.linear_model import LinearRegression
from rpe_calculator import calculate_effective_volume

def load_training_data(filename='training_data.json'):
    """Load training history"""
    with open(filename, 'r') as f:
        return json.load(f)

def prepare_features(training_history):
    """Convert training history into ML features"""
    features = []
    targets = []
    
    for i, session in enumerate(training_history):
        volume_result = calculate_effective_volume(
            session['sets'], 
            session['reps'], 
            session['weight'], 
            session['rpe']
        )
        
        effective_volume = volume_result['effective_volume']
        days_rest = session['days_since_last']
        session_number = i + 1
        
        features.append([effective_volume, days_rest, session_number])
        targets.append(session['weight'])
    
    return np.array(features), np.array(targets)

def predict_next_session(exercise='bench_press', days_until_next=3):
    """Predict next workout performance"""
    data = load_training_data()
    training_history = data[exercise]
    
    X, y = prepare_features(training_history)
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_session = training_history[-1]
    last_volume = calculate_effective_volume(
        last_session['sets'],
        last_session['reps'], 
        last_session['weight'],
        last_session['rpe']
    )['effective_volume']
    
    next_features = [[
        last_volume * 1.02,
        days_until_next,
        len(training_history) + 1
    ]]
    
    predicted_weight = model.predict(next_features)[0]
    r2_score = model.score(X, y)
    
    return {
        'predicted_weight': round(predicted_weight, 1),
        'confidence': round(r2_score * 100, 1)
    }

def main():
    print("🏋️ STRENGTH PREDICTOR - Week 2/260")
    print("=" * 40)
    
    result = predict_next_session('bench_press', days_until_next=4)
    
    print(f"\n📊 Next Bench Press Prediction:")
    print(f"Weight: {result['predicted_weight']}kg x 5 reps")
    print(f"Model Confidence: {result['confidence']}%")

if __name__ == "__main__":
    main()
