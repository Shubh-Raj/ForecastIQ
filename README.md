# ForecastIQ — AI Predictive Forecasting Tool

> Transform historical data into actionable forecasts with confidence ranges, anomaly detection, and scenario comparison.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-Apache%202.0-red)

---

## Overview

**ForecastIQ** is an AI-powered predictive forecasting tool that helps users look ahead instead of backwards. It transforms any time-series CSV dataset into useful forecasts with honest uncertainty ranges, anomaly alerts, and side-by-side scenario comparisons.

Built for the NatWest Hackathon (AI Predictive Forecasting use case), it provides:

- **Short-term forecasting** with confidence intervals (low / likely / high)
- **Anomaly detection** that flags sudden spikes and dips with severity scoring
- **Scenario comparison** to test "what-if" questions before making decisions
- **AI-generated explanations** that non-technical users can understand

The tool is designed to be simple, reliable, and transparent — showing *how* results were produced and *why* certain predictions were made.

---

## Features

- ✅ **Plan Ahead (Short-term Forecasting)** — Generate 1–12 week forecasts with trend decomposition and prediction intervals
- ✅ **Spot Trouble Early (Anomaly Detection)** — Detect unusual data points using Z-score, IQR, and residual analysis with severity scoring (critical/warning)
- ✅ **Compare Plans (Scenario Forecasting)** — Test growth adjustments, outlier removal, and pattern changes with side-by-side visual comparison
- ✅ **Baseline Comparison** — Every forecast is compared to naive baselines (persistence, moving average) to avoid over-fitting
- ✅ **AI Explanations** — Google Gemini-powered natural language summaries (with template fallback when API key is unavailable)
- ✅ **CSV Upload** — Upload your own datasets via drag-and-drop
- ✅ **Auto-detection** — Automatically detects date and value columns in any CSV
- ✅ **Interactive Charts** — Chart.js visualizations with confidence bands and anomaly markers
- ✅ **Dark Mode UI** — Premium glassmorphism design with responsive layout

---

## Tech Stack

| Layer           | Technology                                    |
|-----------------|-----------------------------------------------|
| **Frontend**    | HTML5, CSS3, JavaScript (vanilla), Chart.js   |
| **Backend**     | Python 3.10+, Flask 3.1, Flask-CORS           |
| **Forecasting** | statsmodels (ETS), scikit-learn, numpy, pandas |
| **AI/NLP**      | Google Gemini API (free tier)                  |
| **Data Format** | CSV (bundled samples + user uploads)           |
| **Testing**     | pytest                                         |

---

## Install and Run Instructions

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Natwest
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key (optional — the app works without it using template-based explanations):

```
GEMINI_API_KEY=your_api_key_here
```

Get a free API key at: https://aistudio.google.com/app/apikey

### Step 5: Generate Sample Data

```bash
python scripts/generate_sample_data.py
```

### Step 6: Start the Application

```bash
python src/backend/app.py
```

The app will be available at **http://localhost:5000**

---

## Usage Examples

### 1. Short-term Forecast

1. Select a dataset from the dropdown (e.g., `sample_sales.csv`)
2. Choose the metric column (e.g., `sales`)
3. Set the forecast horizon (e.g., 4 weeks) and confidence level (95%)
4. Click **Generate Forecast**

**Example output:**
> Next 4 weeks: central estimate +6% growth. Lower bound: –2%. Upper bound: +12%. Seasonal spike expected in Week 3.

### 2. Anomaly Detection

1. Navigate to the **Spot Trouble** tab
2. Select your dataset and adjust sensitivity (1=low, 5=high)
3. Click **Detect Anomalies**

**Example output:**
> Found 3 anomalies. 1 critical: sales on 2025-06-09 was unusually high (18,521), 35% above expected range. Investigate potential data entry error or promotional event.

### 3. Scenario Comparison

1. Navigate to the **Compare Plans** tab
2. Adjust the growth slider (e.g., +10%)
3. Toggle "Remove Outliers" if desired
4. Click **Compare Scenarios**

**Example output:**
> Under a +10% growth scenario, total forecast reaches 48,200 (vs 43,800 baseline). Range: 45,100–51,300.

---

## Architecture

The project follows a clean service-oriented architecture:

```
Client (Browser)
    ↓ REST API (JSON)
Flask Backend
    ├── Routes (forecast, anomaly, scenario, dataset)
    ├── Services (forecaster, anomaly_detector, scenario_engine, explainer, baseline)
    └── Utilities (data_loader, validators)
```

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

### Key Design Decisions

1. **ETS over ARIMA**: Exponential Smoothing is more interpretable and performs well on short series with limited history
2. **Multiple anomaly detection methods**: Z-score, IQR, and model residuals are combined to reduce false negatives
3. **Baseline comparison built-in**: Every forecast is automatically compared against naive methods to ensure the model adds value
4. **Template fallback for AI**: The tool works fully without a Gemini API key — explanations gracefully degrade to templates

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_forecaster.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=src/backend --cov-report=term-missing
```

---

## Folder Structure

```
Natwest/
├── README.md                  # This file
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── package.json               # Project metadata
├── src/
│   ├── backend/
│   │   ├── app.py             # Flask application entry point
│   │   ├── config.py          # Centralized configuration
│   │   ├── routes/            # API endpoint handlers
│   │   ├── services/          # Core business logic
│   │   ├── utils/             # Data loading & validation
│   │   └── models/            # Response schemas
│   └── frontend/
│       ├── index.html         # Main HTML page
│       ├── css/styles.css     # Design system & styles
│       └── js/                # Frontend modules
├── data/                      # Sample datasets (CSV)
├── tests/                     # Unit & integration tests
├── docs/                      # Architecture documentation
└── scripts/                   # Utility scripts
```

---

## Limitations

- **No persistent storage**: Data is stored as CSV files; no database is used. Uploaded datasets are lost if the server is restarted without the uploads directory.
- **Single-threaded**: The Flask development server handles one request at a time. For production use, deploy with Gunicorn.
- **Gemini API dependency**: AI explanations require a Gemini API key. Without it, template-based explanations are used (less contextual but still functional).
- **Limited to univariate forecasting**: The tool forecasts one variable at a time. Multivariate forecasting is not supported.

## Future Improvements

- Add database storage (SQLite/PostgreSQL) for persistent dataset management
- Support multivariate time-series forecasting
- Add user authentication and saved forecast history
- Implement Prophet integration for datasets with strong seasonality
- Add export functionality (PDF reports, CSV downloads)
- Deploy as a containerized application (Docker)

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
