# ML Fitness Tools 💪🤖

Week 3/260 of shipping ML code every week.

📅 **Roadmap:** [View all upcoming features here](ROADMAP.md)

## What's This?
I'm building machine learning tools for serious lifters. Every week for 5 years, I'll ship something new that uses ML to make training smarter.

## Completed Projects

**Week 1: RPE Volume Calculator** (Aug 8, 2025)
- Adjusts training volume based on Rate of Perceived Exertion
- Calculates effective training stress, not just weight × reps × sets  
- Foundation for all future predictions

**Week 2: Strength Predictor** (Aug 8, 2025)  
- Linear regression model using training history
- Predicts next workout: 78.8kg × 5 reps
- Model confidence: 100%

**Week 3: Recovery API** (Aug 15, 2025)  
- FastAPI server with REST endpoints
- Recovery score calculation based on sleep, stress, soreness
- HTTP API for RPE calculations and strength predictions
- Auto-generated documentation at `/docs`

## Quick Start
```bash
git clone https://github.com/daleconaghan/ml-fitness-tools.git
cd ml-fitness-tools
pip install -r requirements.txt

# Run the API server
python week3_recovery_api.py

# Or run individual tools
python week2_strength_predictor.py
```

## API Usage

Start the server: `python week3_recovery_api.py`

**Available endpoints:**
- `POST /calculate-rpe` - Calculate RPE-based metrics
- `POST /predict-strength` - Predict next workout strength  
- `POST /recovery-status` - Get recovery score and recommendations
- `GET /health` - API health check
- `GET /docs` - Interactive API documentation

**Example API call:**
```bash
curl -X POST "http://localhost:8000/recovery-status" \
  -H "Content-Type: application/json" \
  -d '{
    "last_session_rpe": 8.5,
    "hours_since_training": 36,
    "sleep_quality": 7.0,
    "stress_level": 4.0,
    "muscle_soreness": 3.0
  }'
```

## The Journey

✅ **Week 1**: RPE Calculator

✅ **Week 2**: Strength Predictor  

✅ **Week 3**: Recovery API

⬜ **Week 4** (Aug 22): Training Load Optimizer

⬜ **Week 5-260**: Building the future of training

---

**Next Week**: ML-powered training load optimization. Automatically adjust volume based on recovery metrics.

Building at the intersection of machine learning and strength training.

Follow: [@daleconaghan](https://twitter.com/daleconaghan)