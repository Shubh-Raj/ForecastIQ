"""
Scenario comparison engine.

Allows users to test different "what-if" scenarios by adjusting
growth rates, removing outliers, or applying different patterns,
then comparing forecasts side by side.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from .forecaster import generate_forecast
from .anomaly_detector import detect_anomalies


def create_scenario_forecast(
    series: pd.Series,
    dates: pd.Series,
    horizon: int = 4,
    confidence: float = 0.95,
    growth_adjustment: float = 0.0,
    remove_outliers: bool = False,
    pattern: str = "trend",
) -> Dict:
    """
    Generate a forecast under a specific scenario.

    Modifies the input data according to the scenario parameters
    before running the forecasting model.

    Args:
        series: Original time series values.
        dates: Corresponding date values.
        horizon: Forecast horizon (periods).
        confidence: Confidence level for intervals.
        growth_adjustment: Fractional growth rate adjustment (e.g. 0.1 = +10%).
        remove_outliers: Whether to remove detected outliers before forecasting.
        pattern: Pattern type ('trend', 'flat', 'seasonal').

    Returns:
        Dictionary with scenario forecast results.
    """
    modified_series = series.copy()

    # Apply outlier removal if requested
    if remove_outliers:
        modified_series = _remove_outliers(modified_series, dates)

    # Apply growth adjustment
    if growth_adjustment != 0:
        modified_series = _apply_growth_adjustment(modified_series, growth_adjustment)

    # Apply pattern modification
    if pattern != "trend":
        modified_series = _apply_pattern(modified_series, pattern)

    # Generate forecast on modified data
    forecast_result = generate_forecast(
        modified_series,
        horizon=horizon,
        confidence=confidence,
    )

    return {
        "scenario_data": modified_series.tolist(),
        "forecast": forecast_result["forecast"],
        "lower_bound": forecast_result["lower_bound"],
        "upper_bound": forecast_result["upper_bound"],
        "model_summary": forecast_result["model_summary"],
    }


def compare_scenarios(
    series: pd.Series,
    dates: pd.Series,
    horizon: int = 4,
    confidence: float = 0.95,
    scenarios: List[Dict] = None,
) -> Dict:
    """
    Generate and compare multiple scenario forecasts side by side.

    Args:
        series: Original time series values.
        dates: Corresponding dates.
        horizon: Forecast horizon.
        confidence: Confidence level for intervals.
        scenarios: List of scenario parameter dictionaries.

    Returns:
        Dictionary with baseline and scenario forecasts for comparison.
    """
    if scenarios is None:
        scenarios = [
            {"name": "Baseline", "growth_adjustment": 0, "remove_outliers": False, "pattern": "trend"},
            {"name": "+10% Growth", "growth_adjustment": 0.1, "remove_outliers": False, "pattern": "trend"},
            {"name": "Outliers Removed", "growth_adjustment": 0, "remove_outliers": True, "pattern": "trend"},
        ]

    # Generate baseline forecast
    baseline = generate_forecast(series, horizon=horizon, confidence=confidence)

    results = {
        "baseline": {
            "name": "Baseline (actual data)",
            "original_data": series.tolist(),
            "forecast": baseline["forecast"],
            "lower_bound": baseline["lower_bound"],
            "upper_bound": baseline["upper_bound"],
            "model_summary": baseline["model_summary"],
        },
        "scenarios": [],
    }

    # Generate each scenario forecast
    for scenario_params in scenarios:
        name = scenario_params.get("name", "Custom Scenario")
        scenario_result = create_scenario_forecast(
            series=series,
            dates=dates,
            horizon=horizon,
            confidence=confidence,
            growth_adjustment=scenario_params.get("growth_adjustment", 0),
            remove_outliers=scenario_params.get("remove_outliers", False),
            pattern=scenario_params.get("pattern", "trend"),
        )

        scenario_result["name"] = name
        results["scenarios"].append(scenario_result)

    # Generate comparison summary
    results["comparison"] = _generate_comparison_summary(
        baseline, results["scenarios"], horizon
    )

    return results


def _remove_outliers(series: pd.Series, dates: pd.Series) -> pd.Series:
    """
    Remove outliers from the series by replacing them with interpolated values.

    Uses the anomaly detector to identify outliers, then replaces them
    with linearly interpolated values.

    Args:
        series: Original time series.
        dates: Corresponding dates.

    Returns:
        Series with outliers replaced.
    """
    result = detect_anomalies(series, dates, sensitivity=3)
    anomaly_indices = [a["index"] for a in result["anomalies"]]

    if not anomaly_indices:
        return series

    cleaned = series.copy()
    cleaned.iloc[anomaly_indices] = np.nan
    cleaned = cleaned.interpolate(method="linear")
    cleaned = cleaned.ffill().bfill()

    return cleaned


def _apply_growth_adjustment(
    series: pd.Series, adjustment: float
) -> pd.Series:
    """
    Apply a growth rate adjustment to the series.

    Scales each point progressively by the adjustment factor.

    Args:
        series: Original time series.
        adjustment: Growth adjustment factor (e.g. 0.1 for +10%).

    Returns:
        Adjusted series.
    """
    n = len(series)
    growth_factors = (1 + adjustment / n) ** np.arange(n)
    return series * growth_factors


def _apply_pattern(series: pd.Series, pattern: str) -> pd.Series:
    """
    Apply a specific pattern to the series.

    Args:
        series: Original time series.
        pattern: 'flat' (removes trend) or 'seasonal' (amplifies seasonality).

    Returns:
        Modified series.
    """
    if pattern == "flat":
        # Remove trend by subtracting linear fit
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series.values, 1)
        trend = np.polyval(coeffs, x)
        mean_val = series.mean()
        detrended = series - trend + mean_val
        return detrended

    elif pattern == "seasonal":
        # Amplify seasonal component
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series.values, 1)
        trend = np.polyval(coeffs, x)
        seasonal_component = series.values - trend
        amplified = trend + seasonal_component * 1.5
        return pd.Series(amplified, index=series.index)

    return series


def _generate_comparison_summary(
    baseline: Dict, scenarios: List[Dict], horizon: int
) -> Dict:
    """
    Generate a summary comparing baseline and scenario forecasts.

    Args:
        baseline: Baseline forecast result.
        scenarios: List of scenario forecast results.
        horizon: Forecast horizon.

    Returns:
        Comparison summary dictionary.
    """
    baseline_total = sum(baseline["forecast"])

    comparisons = []
    for scenario in scenarios:
        scenario_total = sum(scenario["forecast"])
        diff = scenario_total - baseline_total
        diff_pct = (diff / baseline_total * 100) if baseline_total != 0 else 0

        comparisons.append({
            "name": scenario.get("name", "Scenario"),
            "total_forecast": round(scenario_total, 2),
            "difference": round(diff, 2),
            "difference_pct": round(diff_pct, 2),
            "avg_forecast": round(scenario_total / horizon, 2),
        })

    return {
        "baseline_total": round(baseline_total, 2),
        "baseline_avg": round(baseline_total / horizon, 2),
        "scenarios": comparisons,
    }
