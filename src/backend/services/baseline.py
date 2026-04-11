"""
Baseline comparison service.

Implements naive forecasting methods (persistence, seasonal naive, moving average)
to provide a sanity check against more complex models.
This helps avoid over-fitting by showing when simple methods outperform.
"""

import numpy as np
import pandas as pd
from typing import Dict, List


def persistence_forecast(series: pd.Series, horizon: int) -> List[float]:
    """
    Persistence (naive) forecast: repeat the last observed value.

    This is the simplest possible baseline. Any good model should
    beat this on trended or seasonal data.

    Args:
        series: Historical time series values.
        horizon: Number of periods to forecast.

    Returns:
        List of forecasted values (all equal to the last observation).
    """
    last_value = float(series.iloc[-1])
    return [last_value] * horizon


def seasonal_naive_forecast(
    series: pd.Series, horizon: int, seasonal_period: int = None
) -> List[float]:
    """
    Seasonal naive forecast: repeat the last seasonal cycle.

    Uses the values from one full seasonal cycle ago.

    Args:
        series: Historical time series values.
        horizon: Number of periods to forecast.
        seasonal_period: Length of one seasonal cycle.

    Returns:
        List of forecasted values from the last seasonal cycle.
    """
    if seasonal_period is None or seasonal_period >= len(series):
        return persistence_forecast(series, horizon)

    last_cycle = series.iloc[-seasonal_period:].values
    forecast = []
    for i in range(horizon):
        forecast.append(float(last_cycle[i % seasonal_period]))

    return forecast


def moving_average_forecast(
    series: pd.Series, horizon: int, window: int = 4
) -> List[float]:
    """
    Moving average forecast: use the average of the last `window` values.

    A simple smoothing baseline that reduces noise.

    Args:
        series: Historical time series values.
        horizon: Number of periods to forecast.
        window: Number of past periods to average.

    Returns:
        List of forecasted values.
    """
    window = min(window, len(series))
    avg = float(series.iloc[-window:].mean())
    return [avg] * horizon


def compare_with_baseline(
    actual: pd.Series,
    model_forecast: List[float],
    holdout_size: int = None,
) -> Dict:
    """
    Compare model forecast against baseline methods using hold-out validation.

    Splits the data into training and holdout sets, generates forecasts
    from both the model and baselines, and computes error metrics.

    Args:
        actual: Full time series including holdout period.
        model_forecast: Forecasted values from the main model.
        holdout_size: Number of periods to hold out for validation.

    Returns:
        Dictionary with comparison metrics for each method.
    """
    if holdout_size is None:
        holdout_size = min(len(model_forecast), len(actual) // 5)
        holdout_size = max(holdout_size, 1)

    if holdout_size >= len(actual):
        holdout_size = len(actual) // 4

    train = actual.iloc[:-holdout_size]
    holdout = actual.iloc[-holdout_size:]
    holdout_values = holdout.values

    # Adjust model forecast length to match holdout
    model_pred = model_forecast[:holdout_size]
    if len(model_pred) < holdout_size:
        model_pred = model_pred + [model_pred[-1]] * (holdout_size - len(model_pred))

    # Generate baseline forecasts on training data
    persistence = persistence_forecast(train, holdout_size)
    moving_avg = moving_average_forecast(train, holdout_size)

    # Compute metrics for each method
    methods = {
        "model": model_pred,
        "persistence": persistence,
        "moving_average": moving_avg,
    }

    results = {}
    for name, predictions in methods.items():
        pred_array = np.array(predictions[:len(holdout_values)])
        mae = np.mean(np.abs(holdout_values - pred_array))
        rmse = np.sqrt(np.mean((holdout_values - pred_array) ** 2))
        mape = np.mean(np.abs((holdout_values - pred_array) / holdout_values)) * 100

        results[name] = {
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "mape": round(float(mape), 2),
            "predictions": [round(float(v), 2) for v in pred_array],
        }

    # Determine the best method
    best_method = min(results, key=lambda m: results[m]["rmse"])
    results["best_method"] = best_method
    results["model_beats_baseline"] = best_method == "model"

    return results
