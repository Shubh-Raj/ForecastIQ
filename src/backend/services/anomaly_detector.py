"""
Anomaly detection service for time series data.

Identifies unusual spikes and dips using statistical methods:
- Z-score based detection
- IQR (Interquartile Range) method
- Forecast residual analysis

Provides severity scoring and contextual information for each anomaly.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from .forecaster import fit_ets_model


def detect_anomalies(
    series: pd.Series,
    dates: pd.Series,
    sensitivity: int = 3,
    method: str = "combined",
) -> Dict:
    """
    Detect anomalies in a time series using multiple methods.

    Args:
        series: Time series values.
        dates: Corresponding dates for each value.
        sensitivity: Detection sensitivity (1=low, 5=high).
        method: Detection method ('zscore', 'iqr', 'residual', 'combined').

    Returns:
        Dictionary with detected anomalies, their severity, and context.
    """
    anomalies = []

    if method in ("zscore", "combined"):
        z_anomalies = _zscore_detection(series, sensitivity)
        anomalies.extend(z_anomalies)

    if method in ("iqr", "combined"):
        iqr_anomalies = _iqr_detection(series, sensitivity)
        anomalies.extend(iqr_anomalies)

    if method in ("residual", "combined") and len(series) >= 10:
        res_anomalies = _residual_detection(series, sensitivity)
        anomalies.extend(res_anomalies)

    # Merge duplicate indices and assign highest severity
    merged = _merge_anomalies(anomalies)

    # Build results with context
    results = []
    for idx, severity, methods_detected in merged:
        if idx < len(series):
            value = float(series.iloc[idx])
            date_str = str(dates.iloc[idx])

            # Calculate context metrics
            context = _compute_anomaly_context(series, idx)

            results.append({
                "index": int(idx),
                "date": date_str,
                "value": round(value, 2),
                "severity": severity,
                "direction": "spike" if value > series.mean() else "dip",
                "methods": methods_detected,
                "deviation_pct": round(context["deviation_pct"], 2),
                "expected_range": context["expected_range"],
            })

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    results.sort(key=lambda x: severity_order.get(x["severity"], 3))

    # Compute overall summary
    summary = _compute_summary(series, results)

    return {
        "anomalies": results,
        "total_anomalies": len(results),
        "summary": summary,
    }


def _zscore_detection(series: pd.Series, sensitivity: int) -> List[Tuple]:
    """
    Detect anomalies using Z-score method.

    Args:
        series: Time series values.
        sensitivity: Detection sensitivity (1-5).

    Returns:
        List of (index, severity, method) tuples.
    """
    # Map sensitivity to z-score threshold (higher sensitivity = lower threshold)
    thresholds = {1: 3.5, 2: 3.0, 3: 2.5, 4: 2.0, 5: 1.5}
    threshold = thresholds.get(sensitivity, 2.5)

    mean = series.mean()
    std = series.std()

    if std == 0:
        return []

    z_scores = np.abs((series - mean) / std)
    anomalies = []

    for idx in range(len(series)):
        z = z_scores.iloc[idx]
        if z > threshold * 1.5:
            anomalies.append((idx, "critical", "zscore"))
        elif z > threshold:
            anomalies.append((idx, "warning", "zscore"))

    return anomalies


def _iqr_detection(series: pd.Series, sensitivity: int) -> List[Tuple]:
    """
    Detect anomalies using the Interquartile Range method.

    Args:
        series: Time series values.
        sensitivity: Detection sensitivity (1-5).

    Returns:
        List of (index, severity, method) tuples.
    """
    multipliers = {1: 3.0, 2: 2.5, 3: 2.0, 4: 1.5, 5: 1.0}
    multiplier = multipliers.get(sensitivity, 2.0)

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return []

    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr

    anomalies = []
    for idx in range(len(series)):
        val = series.iloc[idx]
        if val < lower_fence or val > upper_fence:
            # Check if extreme
            extreme_lower = q1 - multiplier * 2 * iqr
            extreme_upper = q3 + multiplier * 2 * iqr
            if val < extreme_lower or val > extreme_upper:
                anomalies.append((idx, "critical", "iqr"))
            else:
                anomalies.append((idx, "warning", "iqr"))

    return anomalies


def _residual_detection(series: pd.Series, sensitivity: int) -> List[Tuple]:
    """
    Detect anomalies using fitted model residuals.

    Fits an ETS model and flags points where residuals exceed thresholds.

    Args:
        series: Time series values.
        sensitivity: Detection sensitivity (1-5).

    Returns:
        List of (index, severity, method) tuples.
    """
    try:
        model_result = fit_ets_model(series)
        residuals = model_result.resid
        residual_std = residuals.std()

        if residual_std == 0:
            return []

        thresholds = {1: 3.5, 2: 3.0, 3: 2.5, 4: 2.0, 5: 1.5}
        threshold = thresholds.get(sensitivity, 2.5)

        anomalies = []
        for idx in range(len(residuals)):
            z = abs(residuals.iloc[idx]) / residual_std
            if z > threshold * 1.5:
                anomalies.append((idx, "critical", "residual"))
            elif z > threshold:
                anomalies.append((idx, "warning", "residual"))

        return anomalies
    except Exception:
        return []


def _merge_anomalies(anomaly_list: List[Tuple]) -> List[Tuple]:
    """
    Merge anomalies detected by multiple methods at the same index.

    Args:
        anomaly_list: List of (index, severity, method) tuples.

    Returns:
        Merged list with combined methods and highest severity.
    """
    index_map = {}
    severity_order = {"critical": 0, "warning": 1, "info": 2}

    for idx, severity, method in anomaly_list:
        if idx not in index_map:
            index_map[idx] = {"severity": severity, "methods": [method]}
        else:
            existing = index_map[idx]
            existing["methods"].append(method)
            # Keep highest severity
            if severity_order.get(severity, 3) < severity_order.get(
                existing["severity"], 3
            ):
                existing["severity"] = severity

    return [
        (idx, data["severity"], list(set(data["methods"])))
        for idx, data in sorted(index_map.items())
    ]


def _compute_anomaly_context(series: pd.Series, idx: int) -> Dict:
    """
    Compute contextual information for an anomaly point.

    Args:
        series: Full time series.
        idx: Index of the anomaly.

    Returns:
        Dictionary with deviation percentage and expected range.
    """
    value = series.iloc[idx]
    mean = series.mean()
    std = series.std()

    deviation_pct = ((value - mean) / mean) * 100 if mean != 0 else 0

    return {
        "deviation_pct": deviation_pct,
        "expected_range": {
            "low": round(float(mean - 2 * std), 2),
            "high": round(float(mean + 2 * std), 2),
        },
    }


def _compute_summary(series: pd.Series, anomalies: List[Dict]) -> Dict:
    """
    Compute a summary of the anomaly analysis.

    Args:
        series: Full time series.
        anomalies: List of detected anomaly dictionaries.

    Returns:
        Summary dictionary.
    """
    critical_count = sum(1 for a in anomalies if a["severity"] == "critical")
    warning_count = sum(1 for a in anomalies if a["severity"] == "warning")
    spike_count = sum(1 for a in anomalies if a["direction"] == "spike")
    dip_count = sum(1 for a in anomalies if a["direction"] == "dip")

    return {
        "total_points": len(series),
        "anomaly_rate": round(len(anomalies) / len(series) * 100, 2),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "spike_count": spike_count,
        "dip_count": dip_count,
        "data_mean": round(float(series.mean()), 2),
        "data_std": round(float(series.std()), 2),
    }
