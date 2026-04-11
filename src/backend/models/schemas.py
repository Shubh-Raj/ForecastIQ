"""
Response schemas for API endpoints.

Defines standardized response formats to ensure consistent
API responses across all endpoints.
"""

from typing import Dict, Any, Optional, List


def success_response(
    data: Any,
    message: str = "Success",
    meta: Optional[Dict] = None,
) -> Dict:
    """
    Create a standardized success response.

    Args:
        data: The response payload.
        message: A human-readable success message.
        meta: Optional metadata (e.g. pagination, timing).

    Returns:
        Formatted response dictionary.
    """
    response = {
        "status": "success",
        "message": message,
        "data": data,
    }
    if meta:
        response["meta"] = meta
    return response


def error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Any] = None,
) -> Dict:
    """
    Create a standardized error response.

    Args:
        message: Human-readable error message.
        error_code: Machine-readable error code.
        details: Additional error details.

    Returns:
        Formatted error response dictionary.
    """
    response = {
        "status": "error",
        "message": message,
        "error_code": error_code,
    }
    if details:
        response["details"] = details
    return response


def forecast_response_schema() -> Dict:
    """
    Document the expected shape of a forecast response.

    Returns:
        Schema documentation dictionary.
    """
    return {
        "forecast": "List[float] — central forecast values",
        "lower_bound": "List[float] — lower confidence interval",
        "upper_bound": "List[float] — upper confidence interval",
        "dates": "List[str] — forecast period dates",
        "model_summary": {
            "method": "str — forecasting method used",
            "mape": "float — Mean Absolute Percentage Error",
            "rmse": "float — Root Mean Squared Error",
        },
        "baseline_comparison": {
            "model_beats_baseline": "bool — whether model outperforms baselines",
            "best_method": "str — name of the best performing method",
        },
        "explanation": "str — AI-generated explanation",
    }
