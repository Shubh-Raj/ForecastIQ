"""
Walk-forward backtesting service.

Validates model accuracy by holding out the last N periods,
forecasting them from training data only, then comparing
forecast vs actual values. Answers: "would this model have worked?"
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from .forecaster import generate_forecast


def walk_forward_backtest(
    series: pd.Series,
    dates: pd.Series,
    holdout_size: Optional[int] = None,
    confidence: float = 0.95,
) -> Dict:
    """
    Perform walk-forward backtesting on a time series.

    Splits data into train/holdout, generates a forecast on
    training data, and evaluates accuracy against actual holdout values.

    Args:
        series: Full time series values.
        dates: Corresponding date values.
        holdout_size: Number of periods to hold out. Defaults to 20% of data.
        confidence: Confidence level for prediction intervals.

    Returns:
        Dictionary with holdout actuals, forecasts, accuracy metrics,
        and a hit rate (% of actuals inside confidence band).
    """
    n = len(series)
    if holdout_size is None:
        holdout_size = max(2, min(8, n // 5))

    if n < holdout_size * 3:
        raise ValueError(
            f"Need at least {holdout_size * 3} data points for backtesting "
            f"with holdout_size={holdout_size}. Got {n}."
        )

    train_series = series.iloc[:-holdout_size]
    holdout_series = series.iloc[-holdout_size:]
    holdout_dates = dates.iloc[-holdout_size:]

    # Generate forecast on training data only
    forecast_result = generate_forecast(
        train_series, horizon=holdout_size, confidence=confidence
    )

    forecast_vals = np.array(forecast_result["forecast"])
    lower_vals = np.array(forecast_result["lower_bound"])
    upper_vals = np.array(forecast_result["upper_bound"])
    actual_vals = holdout_series.values

    # Accuracy metrics
    mae = float(np.mean(np.abs(actual_vals - forecast_vals)))
    rmse = float(np.sqrt(np.mean((actual_vals - forecast_vals) ** 2)))
    mape = float(np.mean(np.abs((actual_vals - forecast_vals) / actual_vals)) * 100)

    # Interval hit rate: % of actuals inside confidence band
    hits = int(np.sum((actual_vals >= lower_vals) & (actual_vals <= upper_vals)))
    hit_rate = round(hits / holdout_size * 100, 1)

    # Bias: positive = model over-predicts, negative = under-predicts
    bias = float(np.mean(forecast_vals - actual_vals))

    return {
        "train_dates": dates.iloc[:-holdout_size].dt.strftime("%Y-%m-%d").tolist(),
        "train_values": train_series.tolist(),
        "holdout_dates": holdout_dates.dt.strftime("%Y-%m-%d").tolist(),
        "actual_values": [round(float(v), 2) for v in actual_vals],
        "forecast_values": [round(float(v), 2) for v in forecast_vals],
        "lower_bound": [round(float(v), 2) for v in lower_vals],
        "upper_bound": [round(float(v), 2) for v in upper_vals],
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
            "hit_rate": hit_rate,
            "bias": round(bias, 2),
        },
        "holdout_size": holdout_size,
        "train_size": len(train_series),
        "interpretation": _interpret_metrics(mape, hit_rate, confidence),
    }


def _interpret_metrics(mape: float, hit_rate: float, confidence: float) -> str:
    """Generate a plain-English interpretation of backtest accuracy."""
    expected_hit = confidence * 100
    parts = []

    if mape < 5:
        parts.append(f"Excellent accuracy (MAPE {mape:.1f}% < 5%)")
    elif mape < 10:
        parts.append(f"Good accuracy (MAPE {mape:.1f}%)")
    elif mape < 20:
        parts.append(f"Moderate accuracy (MAPE {mape:.1f}%)")
    else:
        parts.append(f"Low accuracy (MAPE {mape:.1f}% — treat forecasts with caution)")

    if hit_rate >= expected_hit - 10:
        parts.append(
            f"confidence intervals are well-calibrated ({hit_rate}% hit rate)"
        )
    else:
        parts.append(
            f"confidence intervals may be too narrow ({hit_rate}% vs expected {expected_hit:.0f}%)"
        )

    return ". ".join(parts) + "."
