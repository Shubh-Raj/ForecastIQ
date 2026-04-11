# Architecture

## System Overview

ForecastIQ is a full-stack AI-powered predictive forecasting tool built with a Python Flask backend and a vanilla JavaScript frontend. It follows a clean service-oriented architecture where each forecasting use case (planning, anomaly detection, scenario comparison) has its own dedicated service and API route module.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ app.js   │  │forecast.js│  │anomaly.js│  │scenario.js│   │
│  │ (router) │  │(use case)│  │(use case)│  │(use case) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬──────┘   │
│       │              │              │              │         │
│  ┌────▼──────────────▼──────────────▼──────────────▼──────┐  │
│  │                  api.js (HTTP Client)                  │  │
│  └───────────────────────┬───────────────────────────────┘  │
│       Chart.js           │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │ JSON / REST
┌──────────────────────────▼──────────────────────────────────┐
│                     Flask Backend                           │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ /api/      │  │ /api/      │  │ /api/      │            │
│  │ forecast   │  │ anomalies  │  │ scenarios  │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │               │               │                    │
│  ┌─────▼──────┐  ┌─────▼───────┐ ┌─────▼────────┐          │
│  │ forecaster │  │  anomaly    │ │  scenario    │           │
│  │ service    │  │  detector   │ │  engine      │           │
│  └─────┬──────┘  └─────┬───────┘ └─────┬────────┘          │
│        │               │               │                    │
│  ┌─────▼───────────────▼───────────────▼────────┐           │
│  │              baseline service                │           │
│  │         (naive / persistence model)          │           │
│  └──────────────────────────────────────────────┘           │
│        │                                                    │
│  ┌─────▼──────────────────────────┐ ┌────────────────────┐  │
│  │   statsmodels / Prophet        │ │  Gemini API        │  │
│  │   (ETS, Seasonal Decompose)    │ │  (NL Explanations) │  │
│  └────────────────────────────────┘ └────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  data_loader.py — CSV I/O, validation, auto-detect   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Forecast Generation
1. User selects a dataset and configures parameters in the UI
2. Frontend sends POST request to `/api/forecast`
3. Backend loads CSV, auto-detects date/value columns
4. Forecaster service fits an ETS model and generates predictions
5. Baseline service compares model vs naive methods
6. Explainer service generates natural-language summary (via Gemini or templates)
7. Response includes forecast values, confidence bands, decomposition, and explanation

### Anomaly Detection
1. User selects dataset and sensitivity level
2. Backend applies Z-score, IQR, and model residual detection
3. Anomalies are merged across methods, assigned severity
4. Contextual information is computed for each anomaly
5. AI explanation summarizes findings

### Scenario Comparison
1. User adjusts growth rate slider, pattern type, and outlier toggle
2. Backend creates modified copies of the data per scenario
3. Each scenario is forecast independently
4. Comparison summary quantifies differences
5. Side-by-side charts and explanation are returned

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Forecasting model | Exponential Smoothing (ETS) | Well-understood, handles trend + seasonality, interpretable, fast |
| Baseline | Persistence + Moving Average | Simple reference; ensures model adds value |
| Anomaly detection | Z-score + IQR + Residual | Multiple methods reduce false negatives |
| AI explanations | Google Gemini (free tier) | Free, capable NLG, with template fallback |
| Frontend charting | Chart.js | Lightweight, integrates well, supports confidence bands |
| Backend framework | Flask | Simple, well-documented, suitable for API-focused apps |

## Key Design Decisions

1. **Template fallback for AI**: If Gemini API key is not configured, the system uses handcrafted template explanations so the tool remains fully functional without an API key.

2. **Auto-detection of columns**: The data loader automatically detects date and numeric columns, reducing setup friction for users.

3. **Multiple anomaly methods**: Using three independent detection methods and merging results improves robustness.

4. **Progressive prediction intervals**: Forecast uncertainty widens for further-out periods, reflecting real-world uncertainty.

5. **Clean separation of concerns**: Each service is independently testable and has no dependency on Flask or HTTP.
