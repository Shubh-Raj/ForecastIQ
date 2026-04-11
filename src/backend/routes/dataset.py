"""
Dataset management API routes.

Handles listing available datasets, uploading new CSV files,
and retrieving dataset summaries and previews.
"""

import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..utils.data_loader import (
    load_csv,
    get_dataset_summary,
    list_available_datasets,
)
from ..models.schemas import success_response, error_response
from ..config import Config

dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.route("/api/datasets", methods=["GET"])
def list_datasets():
    """
    List all available datasets (bundled samples + uploaded).

    Returns JSON array of dataset objects with name, path, and size.
    """
    try:
        # List datasets from both data and upload directories
        sample_datasets = list_available_datasets(Config.DATA_DIR)
        uploaded_datasets = list_available_datasets(Config.UPLOAD_DIR)

        # Tag them for the frontend
        for ds in sample_datasets:
            ds["source"] = "sample"
        for ds in uploaded_datasets:
            ds["source"] = "uploaded"

        all_datasets = sample_datasets + uploaded_datasets

        return jsonify(success_response(
            data=all_datasets,
            message=f"Found {len(all_datasets)} datasets",
        ))
    except Exception as e:
        return jsonify(error_response(
            message=str(e),
            error_code="DATASET_LIST_ERROR",
        )), 500


@dataset_bp.route("/api/datasets/<filename>/summary", methods=["GET"])
def get_summary(filename):
    """
    Get a summary of a specific dataset.

    Returns column info, date range, and basic statistics.
    """
    try:
        filepath = _resolve_dataset_path(filename)
        df = load_csv(filepath)
        summary = get_dataset_summary(df)
        summary["filename"] = filename

        return jsonify(success_response(data=summary))
    except FileNotFoundError:
        return jsonify(error_response(
            message=f"Dataset '{filename}' not found",
            error_code="DATASET_NOT_FOUND",
        )), 404
    except Exception as e:
        return jsonify(error_response(
            message=str(e),
            error_code="DATASET_SUMMARY_ERROR",
        )), 500


@dataset_bp.route("/api/datasets/<filename>/preview", methods=["GET"])
def preview_dataset(filename):
    """
    Get a preview (first 20 rows) of a dataset.

    Returns the data as a list of dictionaries.
    """
    try:
        filepath = _resolve_dataset_path(filename)
        df = load_csv(filepath)
        preview = df.head(20).to_dict(orient="records")

        return jsonify(success_response(
            data=preview,
            message=f"Preview of {filename} ({len(df)} total rows)",
        ))
    except FileNotFoundError:
        return jsonify(error_response(
            message=f"Dataset '{filename}' not found",
            error_code="DATASET_NOT_FOUND",
        )), 404
    except Exception as e:
        return jsonify(error_response(
            message=str(e),
            error_code="DATASET_PREVIEW_ERROR",
        )), 500


@dataset_bp.route("/api/datasets/upload", methods=["POST"])
def upload_dataset():
    """
    Upload a new CSV dataset.

    Expects a multipart/form-data POST with a 'file' field
    containing the CSV file.
    """
    if "file" not in request.files:
        return jsonify(error_response(
            message="No file provided",
            error_code="NO_FILE",
        )), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error_response(
            message="No file selected",
            error_code="EMPTY_FILENAME",
        )), 400

    if not file.filename.endswith(".csv"):
        return jsonify(error_response(
            message="Only CSV files are accepted",
            error_code="INVALID_FORMAT",
        )), 400

    try:
        filename = secure_filename(file.filename)
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(Config.UPLOAD_DIR, filename)
        file.save(filepath)

        # Validate the uploaded file
        df = load_csv(filepath)
        summary = get_dataset_summary(df)
        summary["filename"] = filename

        return jsonify(success_response(
            data=summary,
            message=f"Dataset '{filename}' uploaded successfully ({len(df)} rows)",
        )), 201
    except Exception as e:
        return jsonify(error_response(
            message=str(e),
            error_code="UPLOAD_ERROR",
        )), 500


def _resolve_dataset_path(filename: str) -> str:
    """
    Resolve a dataset filename to its full path.

    Checks both the sample data directory and uploads directory.

    Args:
        filename: Name of the CSV file.

    Returns:
        Full file path.

    Raises:
        FileNotFoundError: If the file is not found in any location.
    """
    # Check sample data directory
    sample_path = os.path.join(Config.DATA_DIR, filename)
    if os.path.exists(sample_path):
        return sample_path

    # Check uploads directory
    upload_path = os.path.join(Config.UPLOAD_DIR, filename)
    if os.path.exists(upload_path):
        return upload_path

    raise FileNotFoundError(f"Dataset '{filename}' not found")
