"""
Data quality assessment service.

Analyses a time series before forecasting to surface potential issues:
completeness, regularity, stationarity, seasonality strength and
whether there is enough data for reliable forecasting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def assess_data_quality(series: pd.Series, dates: pd.Series) -> Dict:
    """
    Compute a comprehensive data quality report for a time series.

    Args:
        series: Numeric time series values.
        dates: Corresponding datetime values.

    Returns:
        Dictionary with health metrics, a 0-100 health score,
        and plain-English recommendations.
    """
    n = len(series)

    # ── Completeness ──────────────────────────────────────────────
    missing_count = int(series.isna().sum())
    completeness = round((1 - missing_count / n) * 100, 1) if n > 0 else 0.0

    # ── Date regularity ───────────────────────────────────────────
    date_regularity = _compute_date_regularity(dates)

    # ── Stationarity (ADF test) ───────────────────────────────────
    is_stationary, adf_pvalue = _adf_stationarity(series)

    # ── Seasonality strength ──────────────────────────────────────
    seasonality_strength = _compute_seasonality_strength(series)

    # ── Data volume adequacy ──────────────────────────────────────
    sufficient_data = n >= 20
    recommended_min = 30
    volume_score = min(100.0, n / recommended_min * 100)

    # ── Recommended model ─────────────────────────────────────────
    recommended_model = _recommend_model(
        n, seasonality_strength, is_stationary
    )

    # ── Overall health score (weighted average) ───────────────────
    health_score = round(
        completeness * 0.30
        + date_regularity * 0.25
        + volume_score * 0.25
        + (70 if is_stationary is not None else 40) * 0.20,
        1,
    )
    health_score = min(100.0, health_score)

    # ── Grade ─────────────────────────────────────────────────────
    if health_score >= 85:
        grade, grade_color = "A", "success"
    elif health_score >= 70:
        grade, grade_color = "B", "info"
    elif health_score >= 55:
        grade, grade_color = "C", "warning"
    else:
        grade, grade_color = "D", "danger"

    return {
        "health_score": health_score,
        "grade": grade,
        "grade_color": grade_color,
        "data_points": n,
        "sufficient_data": sufficient_data,
        "completeness": completeness,
        "missing_values": missing_count,
        "date_regularity": round(date_regularity, 1),
        "is_stationary": is_stationary,
        "adf_pvalue": round(adf_pvalue, 4) if adf_pvalue is not None else None,
        "seasonality_strength": round(seasonality_strength, 1),
        "recommended_model": recommended_model,
        "warnings": _collect_warnings(
            n, completeness, date_regularity, is_stationary, sufficient_data
        ),
    }


def _compute_date_regularity(dates: pd.Series) -> float:
    """Score how evenly spaced the dates are (100 = perfectly regular)."""
    if len(dates) < 2:
        return 100.0
    diffs = dates.diff().dropna().dt.total_seconds()
    if diffs.mean() == 0:
        return 100.0
    cv = diffs.std() / diffs.mean()  # coefficient of variation
    return max(0.0, (1 - min(cv, 1)) * 100)


def _adf_stationarity(series: pd.Series):
    """Run the Augmented Dickey-Fuller test. Returns (is_stationary, p_value)."""
    clean = series.dropna()
    if len(clean) < 10:
        return None, None
    try:
        from statsmodels.tsa.stattools import adfuller
        result = adfuller(clean, autolag="AIC")
        p_value = float(result[1])
        return p_value < 0.05, p_value
    except Exception:
        return None, None


def _compute_seasonality_strength(series: pd.Series) -> float:
    """Estimate seasonality strength via peak autocorrelation (0–100)."""
    clean = series.dropna()
    if len(clean) < 12:
        return 0.0
    try:
        from statsmodels.tsa.stattools import acf
        max_lag = min(len(clean) // 2, 52)
        autocorr = acf(clean, nlags=max_lag, fft=True)
        # Exclude lag-0 and lag-1 (too local)
        peak = float(max(autocorr[2:], default=0))
        return max(0.0, min(100.0, peak * 100))
    except Exception:
        return 0.0


def _recommend_model(
    n: int, seasonality_strength: float, is_stationary: Optional[bool]
) -> str:
    """Return a recommended model name based on data characteristics."""
    if n < 20:
        return "Moving Average (insufficient data for complex model)"
    if seasonality_strength > 50:
        return "Holt-Winters ETS (strong seasonality detected)"
    if is_stationary is False:
        return "ETS with trend (non-stationary, trending data)"
    if is_stationary is True:
        return "ARIMA(1,1,1) or ETS (stationary series)"
    return "ETS Additive (default)"


def _collect_warnings(
    n: int,
    completeness: float,
    date_regularity: float,
    is_stationary: Optional[bool],
    sufficient_data: bool,
) -> list:
    """Build a list of human-readable warnings about data quality."""
    warnings = []
    if not sufficient_data:
        warnings.append(
            f"Only {n} data points — forecasts may be unreliable. Recommended: 30+"
        )
    if completeness < 95:
        warnings.append(
            f"Missing values detected ({100 - completeness:.1f}% missing). "
            "Gaps have been forward-filled."
        )
    if date_regularity < 80:
        warnings.append(
            "Irregular date spacing detected. Ensure dates represent a consistent frequency."
        )
    return warnings
