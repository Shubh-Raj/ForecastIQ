"""
Core forecasting service using statistical time-series models.

Implements Exponential Smoothing (ETS) and provides prediction intervals
for short-term forecasting with trend and seasonality decomposition.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from typing import Dict, Optional, Tuple, List
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def fit_ets_model(
    series: pd.Series,
    seasonal_periods: Optional[int] = None,
    trend: str = "add",
    seasonal: str = "add",
) -> ExponentialSmoothing:
    """
    Fit an Exponential Smoothing (ETS) model to the time series.

    Automatically detects seasonality period if not provided.
    Falls back to simpler models if the data doesn't support
    full trend + seasonal decomposition.

    Args:
        series: Time series values (numeric).
        seasonal_periods: Number of periods in a seasonal cycle.
        trend: Type of trend component ('add', 'mul', or None).
        seasonal: Type of seasonal component ('add', 'mul', or None).

    Returns:
        Fitted ExponentialSmoothing model results.
    """
    n = len(series)

    # Auto-detect seasonal period if not provided
    if seasonal_periods is None:
        seasonal_periods = _detect_seasonal_period(series)

    # Fall back if not enough data for seasonality
    if seasonal_periods is None or n < 2 * seasonal_periods:
        seasonal = None
        seasonal_periods = None

    try:
        model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        )
        result = model.fit(optimized=True)
        return result
    except Exception:
        # Fallback to simple exponential smoothing
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        return model.fit(optimized=True)


def generate_forecast(
    series: pd.Series,
    horizon: int = 4,
    confidence: float = 0.95,
    seasonal_periods: Optional[int] = None,
) -> Dict:
    """
    Generate a forecast with prediction intervals.

    Args:
        series: Historical time series values.
        horizon: Number of periods to forecast.
        confidence: Confidence level for prediction intervals (e.g. 0.95).
        seasonal_periods: Seasonal period (auto-detected if None).

    Returns:
        Dictionary containing:
        - forecast: list of central predictions
        - lower_bound: lower prediction interval
        - upper_bound: upper prediction interval
        - model_summary: dict with model parameters
        - decomposition: trend and seasonal components
    """
    result = fit_ets_model(series, seasonal_periods=seasonal_periods)

    # Generate point forecast
    forecast = result.forecast(horizon)

    # Calculate prediction intervals using residual standard error
    residuals = result.resid
    residual_std = np.std(residuals)
    z_score = _z_score_for_confidence(confidence)

    # Widen intervals progressively for further-out predictions
    steps = np.arange(1, horizon + 1)
    interval_width = z_score * residual_std * np.sqrt(steps)

    lower_bound = forecast - interval_width
    upper_bound = forecast + interval_width

    # Decompose the original series
    decomposition = _decompose_series(series, seasonal_periods)

    # Calculate model fit metrics
    fitted_values = result.fittedvalues
    mape = np.mean(np.abs((series - fitted_values) / series)) * 100
    rmse = np.sqrt(np.mean((series - fitted_values) ** 2))

    return {
        "forecast": forecast.tolist(),
        "lower_bound": lower_bound.tolist(),
        "upper_bound": upper_bound.tolist(),
        "model_summary": {
            "method": "Exponential Smoothing (ETS)",
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "residual_std": round(residual_std, 2),
            "aic": round(result.aic, 2) if hasattr(result, "aic") else None,
        },
        "decomposition": decomposition,
        "fitted_values": fitted_values.tolist(),
    }


def _detect_seasonal_period(series: pd.Series) -> Optional[int]:
    """
    Attempt to detect the dominant seasonal period using autocorrelation.

    Args:
        series: Time series values.

    Returns:
        Detected seasonal period, or None if no clear seasonality.
    """
    n = len(series)
    if n < 10:
        return None

    try:
        from statsmodels.tsa.stattools import acf

        max_lag = min(n // 2, 52)
        autocorr = acf(series, nlags=max_lag, fft=True)

        # Find peaks in autocorrelation (excluding lag 0)
        peaks = []
        for i in range(2, len(autocorr) - 1):
            if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
                if autocorr[i] > 0.1:  # Minimum correlation threshold
                    peaks.append((i, autocorr[i]))

        if peaks:
            # Return the lag with highest autocorrelation
            best_period = max(peaks, key=lambda x: x[1])[0]
            return best_period
    except Exception:
        pass

    return None


def _decompose_series(
    series: pd.Series, seasonal_periods: Optional[int] = None
) -> Dict:
    """
    Decompose the time series into trend, seasonal, and residual components.

    Args:
        series: Time series values.
        seasonal_periods: Period for seasonal decomposition.

    Returns:
        Dictionary with trend, seasonal, and residual arrays.
    """
    if seasonal_periods is None:
        seasonal_periods = _detect_seasonal_period(series)

    if seasonal_periods is None or len(series) < 2 * seasonal_periods:
        # Return simple moving average as trend
        window = min(5, len(series) // 2)
        if window < 2:
            window = 2
        trend = series.rolling(window=window, center=True).mean()
        trend_filled = trend.ffill().bfill()
        return {
            "trend": trend_filled.tolist(),
            "seasonal": [0] * len(series),
            "residual": (series - trend_filled).tolist(),
        }

    try:
        decomposition = seasonal_decompose(
            series, model="additive", period=seasonal_periods
        )
        return {
            "trend": decomposition.trend.ffill().bfill().tolist(),
            "seasonal": decomposition.seasonal.fillna(0).tolist(),
            "residual": decomposition.resid.fillna(0).tolist(),
        }
    except Exception:
        return {
            "trend": series.tolist(),
            "seasonal": [0] * len(series),
            "residual": [0] * len(series),
        }


def _z_score_for_confidence(confidence: float) -> float:
    """
    Get the z-score for a given confidence level.

    Args:
        confidence: Confidence level (e.g. 0.95).

    Returns:
        Corresponding z-score.
    """
    from scipy import stats

    return stats.norm.ppf((1 + confidence) / 2)
