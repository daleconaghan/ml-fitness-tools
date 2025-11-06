# ML Fitness Tools 💪🤖

[![CI/CD Pipeline](https://github.com/daleconaghan/ml-fitness-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/daleconaghan/ml-fitness-tools/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen)](https://github.com/daleconaghan/ml-fitness-tools)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Week 4/260 of shipping ML code every week.

📅 **Roadmap:** [View all upcoming features here](ROADMAP.md)

## What's This?
I'm building machine learning tools for serious lifters. Every week for 5 years, I'll ship something new that uses ML to make training smarter.

## Completed Projects

**Week 1: RPE Volume Calculator** (Sep 5, 2025)
- Adjusts training volume based on Rate of Perceived Exertion
- Calculates effective training stress, not just weight × reps × sets
- Foundation for all future predictions

**Week 2: Strength Predictor** (Sep 12, 2025)
- Linear regression model using training history
- Predicts next workout: 78.8kg × 5 reps
- Model confidence: 100%

**Week 3: Recovery API** (Sep 19, 2025)
- FastAPI server with REST endpoints
- Recovery score calculation based on sleep, stress, soreness
- HTTP API for RPE calculations and strength predictions
- Auto-generated documentation at `/docs`

**Week 4: Overtraining Risk Detector** (Sep 26, 2025)
- Advanced ML algorithm detecting overtraining risk (0-100%)
- Multi-factor analysis: training load trends, RPE inflation, recovery metrics
- Risk levels: Low/Moderate/High/Critical with deload recommendations
- New `/overtraining-risk` API endpoint

## Quick Start
```bash
git clone https://github.com/daleconaghan/ml-fitness-tools.git
cd ml-fitness-tools
pip install -r requirements.txt

# Run the API server
python recovery_api.py

# Or run individual tools (standalone versions)
python standalone/rpe_calculator.py
python standalone/week2_strength_predictor.py

# Run tests
pytest tests/
```

## Configuration

The API can be configured using environment variables:

```bash
# Set allowed CORS origins (comma-separated)
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"

# Set API host and port
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

See `.env.example` for all available configuration options.

## Development

### Setup Development Environment

```bash
# Install development dependencies
make install-dev

# Or manually:
pip install -r requirements-dev.txt
pre-commit install
```

### Common Commands

```bash
make test          # Run all tests
make test-cov      # Run tests with coverage report
make lint          # Check code quality
make format        # Auto-format code
make security      # Run security checks
make ci            # Run all CI checks locally
make run           # Start the API server
```

### Running CI Checks Locally

Before pushing, run all CI checks:

```bash
make ci
```

This runs the same tests, linting, and security checks that GitHub Actions will run.

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The hooks will:
- Format code with Black
- Sort imports with isort
- Lint with Ruff
- Check for security issues with Bandit
- Run tests

## API Usage

Start the server: `python recovery_api.py`

**Available endpoints:**
- `POST /calculate-rpe` - Calculate RPE-based metrics
- `POST /predict-strength` - Predict next workout strength  
- `POST /recovery-status` - Get recovery score and recommendations
- `POST /overtraining-risk` - Detect overtraining risk with recommendations
- `GET /health` - API health check
- `GET /docs` - Interactive API documentation

**Example API calls:**
```bash
# Check recovery status
curl -X POST "http://localhost:8000/recovery-status" \
  -H "Content-Type: application/json" \
  -d '{
    "last_session_rpe": 8.5,
    "hours_since_training": 36,
    "sleep_quality": 7.0,
    "stress_level": 4.0,
    "muscle_soreness": 3.0
  }'

# Detect overtraining risk
curl -X POST "http://localhost:8000/overtraining-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "recent_sessions": [
      {"weight": 225, "reps": 5, "rpe": 8.5},
      {"weight": 230, "reps": 5, "rpe": 9.0}
    ],
    "sleep_quality_avg": 6,
    "stress_level_avg": 7,
    "motivation_level": 4,
    "resting_hr_trend": 8
  }'
```

## The Journey

✅ **Week 1**: RPE Calculator

✅ **Week 2**: Strength Predictor

✅ **Week 3**: Recovery API

✅ **Week 4**: Overtraining Risk Detector

⬜ **Week 5** (Oct 3): Workout Plan Recommender

⬜ **Week 6-260**: Building the future of training

---

**Next Week**: Auto-generated workout plans. ML recommends weekly training based on your last 4 weeks of data.

Building at the intersection of machine learning and strength training.

Follow: [@daleconaghan](https://twitter.com/daleconaghan)