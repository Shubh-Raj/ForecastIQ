"""
Backtest API route — walk-forward validation endpoint.
Data quality API route — data health score endpoint.
"""

import os
from flask import Blueprint, request, jsonify
from ..utils.data_loader import load_csv, prepare_time_series
from ..utils.validators import validate_forecast_params
from ..services.backtester import walk_forward_backtest
from ..services.data_quality import assess_data_quality
from ..services.model_comparison import compare_models
from ..models.schemas import success_response, error_response
from ..config import Config

extras_bp = Blueprint("extras", __name__)


@extras_bp.route("/api/backtest", methods=["POST"])
def backtest():
    """
    Walk-forward backtest endpoint.

    Request body (JSON):
        - dataset: str
        - value_column: str (optional)
        - holdout_size: int (optional, default auto)
        - confidence: float (optional, default 0.95)

    Returns forecast vs actuals for the holdout period with accuracy metrics.
    """
    try:
        params = request.get_json(force=True)
        validated = validate_forecast_params(params)
    except ValueError as e:
        return jsonify(error_response(str(e), "VALIDATION_ERROR")), 400

    dataset = validated.get("dataset")
    if not dataset:
        return jsonify(error_response("Dataset required", "MISSING_DATASET")), 400

    try:
        filepath = _resolve_path(dataset)
        df = load_csv(filepath)
        df, date_col, value_col = prepare_time_series(
            df, value_col=validated.get("value_column")
        )
        holdout_size = int(params.get("holdout_size", 0)) or None

        result = walk_forward_backtest(
            series=df[value_col],
            dates=df[date_col],
            holdout_size=holdout_size,
            confidence=validated["confidence"],
        )
        result["column"] = value_col
        return jsonify(success_response(data=result, message="Backtest complete"))

    except FileNotFoundError:
        return jsonify(error_response(f"Dataset '{dataset}' not found", "DATASET_NOT_FOUND")), 404
    except ValueError as e:
        return jsonify(error_response(str(e), "BACKTEST_ERROR")), 400
    except Exception as e:
        return jsonify(error_response(str(e), "BACKTEST_ERROR")), 500


@extras_bp.route("/api/data-quality", methods=["POST"])
def data_quality():
    """
    Data quality assessment endpoint.

    Request body (JSON):
        - dataset: str
        - value_column: str (optional)

    Returns a health score, quality metrics, and warnings.
    """
    try:
        params = request.get_json(force=True)
    except Exception:
        return jsonify(error_response("Invalid JSON", "BAD_REQUEST")), 400

    dataset = params.get("dataset")
    if not dataset:
        return jsonify(error_response("Dataset required", "MISSING_DATASET")), 400

    try:
        filepath = _resolve_path(dataset)
        df = load_csv(filepath)
        df, date_col, value_col = prepare_time_series(
            df, value_col=params.get("value_column")
        )
        result = assess_data_quality(df[value_col], df[date_col])
        result["column"] = value_col
        return jsonify(success_response(data=result, message="Quality assessment complete"))

    except FileNotFoundError:
        return jsonify(error_response(f"Dataset '{dataset}' not found", "DATASET_NOT_FOUND")), 404
    except Exception as e:
        return jsonify(error_response(str(e), "QUALITY_ERROR")), 500


@extras_bp.route("/api/model-comparison", methods=["POST"])
def model_comparison():
    """
    Multi-model forecasting comparison endpoint.

    Runs ETS, ARIMA and Moving Average, returns accuracy leaderboard
    and the best model's forecast.

    Request body (JSON):
        - dataset: str
        - value_column: str (optional)
        - horizon: int (optional, default 4)
        - confidence: float (optional, default 0.95)
    """
    try:
        params = request.get_json(force=True)
        validated = validate_forecast_params(params)
    except ValueError as e:
        return jsonify(error_response(str(e), "VALIDATION_ERROR")), 400

    dataset = validated.get("dataset")
    if not dataset:
        return jsonify(error_response("Dataset required", "MISSING_DATASET")), 400

    try:
        import pandas as pd
        filepath = _resolve_path(dataset)
        df = load_csv(filepath)
        df, date_col, value_col = prepare_time_series(
            df, value_col=validated.get("value_column")
        )

        result = compare_models(
            series=df[value_col],
            horizon=validated["horizon"],
            confidence=validated["confidence"],
        )

        # Add date info for frontend
        last_date = pd.to_datetime(df[date_col].iloc[-1])
        diff_days = (df[date_col].iloc[-1] - df[date_col].iloc[-2]).days
        freq = "W" if diff_days <= 7 else "MS" if diff_days <= 31 else "D"
        forecast_dates = pd.date_range(
            start=last_date + pd.tseries.frequencies.to_offset(freq),
            periods=validated["horizon"],
            freq=freq,
        )
        result["historical_dates"] = df[date_col].dt.strftime("%Y-%m-%d").tolist()
        result["historical_values"] = df[value_col].tolist()
        result["forecast_dates"] = forecast_dates.strftime("%Y-%m-%d").tolist()
        result["column"] = value_col

        return jsonify(success_response(data=result, message="Model comparison complete"))

    except FileNotFoundError:
        return jsonify(error_response(f"Dataset '{dataset}' not found", "DATASET_NOT_FOUND")), 404
    except Exception as e:
        return jsonify(error_response(str(e), "COMPARISON_ERROR")), 500


def _resolve_path(filename: str) -> str:
    for directory in [Config.DATA_DIR, Config.UPLOAD_DIR]:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Dataset '{filename}' not found")
