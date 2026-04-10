"""
Input validation utilities for API endpoints.

Provides validation functions for request parameters
to ensure data integrity and security.
"""

from typing import Optional, Dict, Any, List


def validate_forecast_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize forecast request parameters.

    Args:
        params: Raw request parameters from the API.

    Returns:
        Validated and normalized parameters.

    Raises:
        ValueError: If any parameter is invalid.
    """
    validated = {}

    # Horizon (number of periods to forecast)
    horizon = params.get("horizon", 4)
    try:
        horizon = int(horizon)
    except (TypeError, ValueError):
        raise ValueError("Horizon must be an integer.")
    if horizon < 1 or horizon > 52:
        raise ValueError("Horizon must be between 1 and 52 periods.")
    validated["horizon"] = horizon

    # Confidence level
    confidence = params.get("confidence", 0.95)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError("Confidence level must be a number.")
    if confidence < 0.5 or confidence > 0.99:
        raise ValueError("Confidence level must be between 0.5 and 0.99.")
    validated["confidence"] = confidence

    # Dataset name
    dataset = params.get("dataset")
    if dataset and not dataset.endswith(".csv"):
        raise ValueError("Dataset must be a CSV file.")
    validated["dataset"] = dataset

    # Value column
    validated["value_column"] = params.get("value_column")

    return validated


def validate_scenario_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate scenario comparison parameters.

    Args:
        params: Raw request parameters.

    Returns:
        Validated parameters.

    Raises:
        ValueError: If parameters are invalid.
    """
    validated = validate_forecast_params(params)

    # Growth rate adjustment (-50% to +100%)
    growth_adjustment = params.get("growth_adjustment", 0)
    try:
        growth_adjustment = float(growth_adjustment)
    except (TypeError, ValueError):
        raise ValueError("Growth adjustment must be a number.")
    if growth_adjustment < -50 or growth_adjustment > 100:
        raise ValueError("Growth adjustment must be between -50 and 100 percent.")
    validated["growth_adjustment"] = growth_adjustment / 100.0

    # Remove outliers flag
    validated["remove_outliers"] = bool(params.get("remove_outliers", False))

    # Pattern type: 'flat', 'seasonal', 'trend'
    pattern = params.get("pattern", "trend")
    if pattern not in ("flat", "seasonal", "trend"):
        raise ValueError("Pattern must be one of: flat, seasonal, trend.")
    validated["pattern"] = pattern

    return validated


def validate_anomaly_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate anomaly detection parameters.

    Args:
        params: Raw request parameters.

    Returns:
        Validated parameters.

    Raises:
        ValueError: If parameters are invalid.
    """
    validated = {}

    # Dataset name
    dataset = params.get("dataset")
    if dataset and not dataset.endswith(".csv"):
        raise ValueError("Dataset must be a CSV file.")
    validated["dataset"] = dataset

    # Value column
    validated["value_column"] = params.get("value_column")

    # Sensitivity (1-5, where 5 is most sensitive)
    sensitivity = params.get("sensitivity", 3)
    try:
        sensitivity = int(sensitivity)
    except (TypeError, ValueError):
        raise ValueError("Sensitivity must be an integer.")
    if sensitivity < 1 or sensitivity > 5:
        raise ValueError("Sensitivity must be between 1 and 5.")
    validated["sensitivity"] = sensitivity

    return validated
