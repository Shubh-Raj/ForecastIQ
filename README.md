# ForecastIQ — AI Predictive Forecasting Tool

> Turn any time-series CSV into actionable forecasts with honest uncertainty ranges, anomaly alerts, scenario comparison, walk-forward backtesting, and multi-model selection.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-Apache%202.0-red)
![Tests](https://img.shields.io/badge/tests-50%20passing-brightgreen)
![PWA](https://img.shields.io/badge/PWA-installable-purple)

---

## Overview

**ForecastIQ** is an AI-powered predictive forecasting tool that helps users look ahead instead of backwards. It transforms any time-series CSV dataset into useful forecasts with honest uncertainty ranges, anomaly alerts, side-by-side scenario comparisons, and statistical validation — all explained in plain English.

Built for the NatWest Hackathon (AI Predictive Forecasting track), it implements all three required use cases with additional professional-grade features that separate it from the crowd.

---

## Features

### Core Use Cases
- ✅ **Plan Ahead (Short-term Forecasting)** — Exponential Smoothing (ETS) forecasts 1–12 periods ahead with low/likely/high confidence bands and seasonal decomposition
- ✅ **Spot Trouble Early (Anomaly Detection)** — Detects unusual spikes and dips using three independent methods (Z-score, IQR, residual analysis) with severity scoring (critical/warning) and deviation percentage
- ✅ **Compare Plans (Scenario Forecasting)** — Side-by-side scenario forecasts with growth-rate sliders, pattern adjustments (trend/flat/seasonal), and outlier removal

### Differentiating Features
- 🏆 **Multi-Model Horse Race** — Runs ETS vs ARIMA(1,1,1) vs Moving Average simultaneously, ranks them by MAPE on a hold-out set, and uses the winner automatically
- 🔬 **Walk-Forward Backtesting** — Validates accuracy on held-out historical data before trusting any forecast. Shows MAE, RMSE, MAPE, hit rate (% of actuals inside confidence band), and bias
- 📊 **Data Health Score** — Before every analysis, automatically runs ADF stationarity test, checks completeness, date regularity, and seasonality strength. Assigns an A–D grade with plain-English warnings
- 🚨 **Alert Threshold / Early Warning** — User sets a threshold (e.g. "warn me if sales drop below 8,000"). If the forecast lower bound crosses it, a red banner shows immediately
- ⬇ **CSV Export** — Download forecast and anomaly results as spreadsheet-ready CSV files with one click
- 📱 **Progressive Web App (PWA)** — Installable on desktop and mobile with offline caching for static assets
- 🤖 **AI Explanations** — Google Gemini API generates plain-English summaries; gracefully falls back to intelligent templates when the API key is absent
- 📋 **Baseline Comparison** — Every forecast is compared against naive baselines (persistence, moving average) to prove the model adds value
- 🔄 **Auto-column detection** — Automatically detects date and numeric columns in any CSV — no manual mapping required

---

## Tech Stack

| Layer           | Technology                                          |
|-----------------|-----------------------------------------------------|
| **Frontend**    | HTML5, CSS3, JavaScript (vanilla), Chart.js 4.x     |
| **Backend**     | Python 3.12, Flask 3.1, Flask-CORS                  |
| **Forecasting** | statsmodels (ETS, ARIMA), scikit-learn, numpy, pandas, scipy |
| **AI / NLP**    | Google Gemini API (free tier) + template fallback   |
| **Testing**     | pytest (50 tests)                                   |
| **Data format** | CSV (bundled samples + drag-and-drop upload)        |
| **Deployment**  | Flask dev server / Gunicorn (production)            |

---

## Install and Run

### Prerequisites

| Requirement | Minimum |
|-------------|---------|
| Python | 3.10+ |
| pip | any |
| Git | any |
| Browser | Chrome / Firefox / Edge (modern) |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/forecastiq.git
cd forecastiq
```

### Step 2 — Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

> **Note (Ubuntu/Debian):** If `python3-venv` is not installed, run:
> `sudo apt install python3.12-venv python3-pip`

If `pip` is not available in your environment:
```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --user
```

### Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

All required packages are pinned in `requirements.txt`. Key dependencies:

| Package | Purpose |
|---------|---------|
| `flask` | Web framework and API server |
| `flask-cors` | Cross-origin request handling |
| `pandas` | Data loading and manipulation |
| `numpy` | Numerical computations |
| `statsmodels` | ETS and ARIMA forecasting models |
| `scikit-learn` | Preprocessing utilities |
| `scipy` | Statistical tests (z-scores, ADF) |
| `google-generativeai` | Gemini AI explanations |
| `python-dotenv` | Environment variable loading |
| `gunicorn` | Production WSGI server |
| `pytest` | Testing framework |

### Step 4 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`. The only optional setting is the Gemini API key — the tool works fully without it using template-based explanations:

```env
GEMINI_API_KEY=your_key_here      # Optional — get free key at aistudio.google.com
FLASK_ENV=development
FLASK_PORT=5000
DATA_DIR=data
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=16
```

> ⚠️ **Never commit your `.env` file** — it is already listed in `.gitignore`

### Step 5 — Generate Sample Datasets

```bash
python3 scripts/generate_sample_data.py
```

This creates three realistic CSV files in `data/`:
- `sample_sales.csv` — 52 weeks of weekly sales with trend + seasonality (weekly)
- `sample_traffic.csv` — 180 days of web traffic with weekly cycles and anomalies (daily)
- `sample_usage.csv` — 36 months of resource usage with upward trend (monthly)

### Step 6 — Start the Application

```bash
python3 src/backend/app.py
```

Open your browser at **http://localhost:5000**

For production:
```bash
gunicorn -w 2 -b 0.0.0.0:5000 "src.backend.app:create_app()"
```

---

## Usage Guide

### Plan Ahead (Forecast Tab)

1. Select a dataset from the dropdown
2. Choose the metric column (auto-detected from CSV)
3. Set the forecast horizon (2–12 periods) and confidence level (80–99%)
4. *(Optional)* Enter an Alert Threshold — get a red warning banner if the pessimistic (lower bound) forecast drops below it
5. Click **Generate Forecast** → see forecast + confidence bands, trend direction, model accuracy, and AI explanation
6. Click **🏆 Model Race** → compare ETS vs ARIMA vs Moving Average with a ranked leaderboard
7. Click **Run Backtest** → validate accuracy on held-out historical periods

### Spot Trouble (Anomaly Tab)

1. Navigate to the **Spot Trouble** tab
2. Adjust sensitivity (1 = only extreme outliers, 5 = flag subtle variations)
3. Click **Detect Anomalies** → chart highlights critical (red triangles) and warning (orange circles) events
4. Click **⬇ Export CSV** → download the anomaly list as a CSV file

### Compare Plans (Scenario Tab)

1. Navigate to **Compare Plans**
2. Adjust the growth slider (–50% to +100%)
3. Choose a pattern type (Keep Trend / Remove Trend / Amplify Seasonality)
4. Toggle "Remove Outliers" to test cleaner-data scenarios
5. Click **Compare Scenarios** → side-by-side chart with quantitative comparison cards

### Upload Your Own Data

Click **Upload** in the header. Drag and drop any CSV file with at least:
- One date/datetime column (any common format is auto-detected)
- One or more numeric columns

---

## Running Tests

```bash
# Run all 50 tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_forecaster.py -v

# With coverage (if pytest-cov installed)
pytest tests/ --cov=src/backend --cov-report=term-missing
```

### Test Summary

| File | Tests | What is covered |
|------|-------|----------------|
| `test_data_loader.py` | 14 | CSV loading, column detection, validation, listing |
| `test_forecaster.py` | 13 | ETS fitting, interval widths, decomposition, MAPE |
| `test_anomaly_detector.py` | 9 | Z-score, IQR, merge logic, severity assignment |
| `test_scenario_engine.py` | 14 | Growth adjustment, pattern types, comparison summary |
| `test_api.py` | — | Flask test client integration tests |

---

## Folder Structure

```
forecastiq/
├── README.md                       # This file
├── LICENSE                         # Apache License 2.0
├── CONTRIBUTING.md                 # DCO sign-off guide
├── .env.example                    # Environment variable template (no secrets)
├── .gitignore                      # Ignores .env, uploads/, venv/, __pycache__
├── requirements.txt                # Python dependencies
├── package.json                    # Project metadata
├── pytest.ini                      # Test configuration
│
├── src/
│   ├── backend/
│   │   ├── app.py                  # Flask app factory + blueprint registration
│   │   ├── config.py               # Centralised env-var configuration
│   │   ├── models/
│   │   │   └── schemas.py          # Standardised API response schemas
│   │   ├── routes/
│   │   │   ├── forecast.py         # POST /api/forecast
│   │   │   ├── anomaly.py          # POST /api/anomalies
│   │   │   ├── scenario.py         # POST /api/scenarios
│   │   │   ├── dataset.py          # GET/POST /api/datasets
│   │   │   └── extras.py           # /api/backtest, /api/data-quality, /api/model-comparison
│   │   ├── services/
│   │   │   ├── forecaster.py       # ETS model fitting + prediction intervals
│   │   │   ├── anomaly_detector.py # Z-score + IQR + residual multi-method detection
│   │   │   ├── scenario_engine.py  # What-if scenario forecasting
│   │   │   ├── backtester.py       # Walk-forward validation
│   │   │   ├── model_comparison.py # ETS vs ARIMA vs Moving Average race
│   │   │   ├── data_quality.py     # ADF stationarity, completeness, health score
│   │   │   ├── baseline.py         # Naive persistence + moving average baselines
│   │   │   └── explainer.py        # Gemini AI explanations + template fallback
│   │   └── utils/
│   │       ├── data_loader.py      # CSV loading, column auto-detection
│   │       └── validators.py       # API parameter validation
│   │
│   └── frontend/
│       ├── index.html              # Single-page application
│       ├── manifest.json           # PWA manifest (installable app)
│       ├── sw.js                   # Service worker (offline caching)
│       ├── css/
│       │   └── styles.css          # Full design system (1200+ lines)
│       └── js/
│           ├── api.js              # HTTP client wrapper for all endpoints
│           ├── charts.js           # Chart.js rendering utilities
│           ├── forecast.js         # Plan Ahead tab logic
│           ├── anomaly.js          # Spot Trouble tab logic
│           ├── scenario.js         # Compare Plans tab logic
│           ├── backtest.js         # Walk-forward backtest rendering
│           ├── model_race.js       # Multi-model leaderboard rendering
│           ├── extras.js           # Data quality, threshold alert, CSV export
│           └── app.js              # Tab router, upload modal, toasts
│
├── data/                           # Bundled sample CSV datasets
│   ├── sample_sales.csv            # 52-row weekly sales
│   ├── sample_traffic.csv          # 180-row daily web traffic
│   └── sample_usage.csv            # 36-row monthly resource usage
│
├── tests/                          # pytest test suite
│   ├── test_data_loader.py
│   ├── test_forecaster.py
│   ├── test_anomaly_detector.py
│   ├── test_scenario_engine.py
│   └── test_api.py
│
├── docs/
│   └── architecture.md             # System architecture diagram + design decisions
│
└── scripts/
    └── generate_sample_data.py     # Generates all sample datasets
```

---

## API Reference

All endpoints return a consistent JSON envelope:

```json
{
  "status": "success" | "error",
  "message": "...",
  "data": { ... }
}
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/datasets` | List all available datasets |
| `GET` | `/api/datasets/<name>/summary` | Dataset schema + stats |
| `GET` | `/api/datasets/<name>/preview` | First N rows |
| `POST` | `/api/datasets/upload` | Upload a CSV file |
| `POST` | `/api/forecast` | Generate ETS forecast |
| `POST` | `/api/anomalies` | Detect anomalies |
| `POST` | `/api/scenarios` | Compare scenarios |
| `POST` | `/api/backtest` | Walk-forward validation |
| `POST` | `/api/data-quality` | Data health score |
| `POST` | `/api/model-comparison` | ETS vs ARIMA vs MA race |

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system diagram.

### Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Forecasting model | ETS (Exponential Smoothing) | Interpretable, handles trend + seasonality, no manual parameter tuning |
| Anomaly detection | Z-score + IQR + Residual (merged) | Three independent methods reduce false negatives |
| Model validation | Walk-forward backtest | Only honest way to evaluate forecasting accuracy |
| Multi-model | ETS + ARIMA + MA leaderboard | No single model is always best; shows awareness |
| AI explanations | Gemini API + template fallback | Free tier; app works fully without a key |
| Frontend | Vanilla JS (no framework) | Lightweight, no build step, runs anywhere |
| Security | No hardcoded secrets, `.env` only | API keys never committed |

---

## Limitations

- Single-variable (univariate) forecasting only; multivariate models not supported
- Flask development server is single-threaded; use Gunicorn for concurrent users
- No persistent database; uploaded files are session-local
- ETS/ARIMA accuracy depends on data volume (≥20 points recommended; ≥30 for reliable intervals)
- Gemini API has rate limits on the free tier; template explanations are always available

## Future Improvements

- PostgreSQL/SQLite dataset persistence
- Multivariate and multi-step forecasting
- Prophet integration for holiday/event-aware forecasting
- User authentication and saved forecast history
- Docker container for one-command deployment
- PDF report generation with embedded charts
- Real-time data streaming via WebSocket

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for DCO sign-off requirements and code style guidelines.

## Acknowledgements

Built with [statsmodels](https://www.statsmodels.org/), [Chart.js](https://www.chartjs.org/), [Flask](https://flask.palletsprojects.com/), and [Google Gemini](https://aistudio.google.com/).
