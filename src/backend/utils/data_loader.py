"""
Data loader utility for reading, validating, and preprocessing CSV datasets.

Handles both bundled sample data and user-uploaded files with
robust error handling and type detection.
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict


def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        filepath: Absolute or relative path to the CSV file.

    Returns:
        DataFrame with the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {e}")

    if df.empty:
        raise ValueError("CSV file is empty")

    return df


def detect_date_column(df: pd.DataFrame) -> Optional[str]:
    """
    Automatically detect the date/time column in a DataFrame.

    Looks for columns named 'date', 'timestamp', 'time', 'dt', 'period'
    or columns that can be parsed as datetime.

    Args:
        df: Input DataFrame.

    Returns:
        Name of the detected date column, or None.
    """
    date_keywords = ["date", "timestamp", "time", "dt", "period", "day", "month", "week"]

    # Check column names first
    for col in df.columns:
        if col.lower().strip() in date_keywords:
            return col

    # Try parsing each column as datetime
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                pd.to_datetime(df[col].head(10))
                return col
            except (ValueError, TypeError):
                continue

    return None


def detect_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify numeric columns suitable for forecasting.

    Args:
        df: Input DataFrame.

    Returns:
        List of numeric column names.
    """
    return df.select_dtypes(include=[np.number]).columns.tolist()


def prepare_time_series(
    df: pd.DataFrame,
    date_col: Optional[str] = None,
    value_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, str, str]:
    """
    Prepare a DataFrame for time series analysis.

    Detects date and value columns if not specified, sorts by date,
    and handles missing values.

    Args:
        df: Input DataFrame.
        date_col: Name of the date column (auto-detected if None).
        value_col: Name of the value column (auto-detected if None).

    Returns:
        Tuple of (prepared DataFrame, date column name, value column name).

    Raises:
        ValueError: If date or value columns cannot be determined.
    """
    # Auto-detect date column
    if date_col is None:
        date_col = detect_date_column(df)
    if date_col is None:
        raise ValueError(
            "Could not detect a date column. "
            "Please ensure your CSV has a column named 'date'."
        )

    # Auto-detect value column
    if value_col is None:
        numeric_cols = detect_numeric_columns(df)
        if not numeric_cols:
            raise ValueError("No numeric columns found for forecasting.")
        value_col = numeric_cols[0]

    # Parse dates and sort
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    # Handle missing values with forward fill, then backward fill
    df[value_col] = df[value_col].ffill().bfill()

    return df, date_col, value_col


def get_dataset_summary(df: pd.DataFrame) -> Dict:
    """
    Generate a summary of a dataset for the frontend.

    Args:
        df: Input DataFrame.

    Returns:
        Dictionary with dataset metadata.
    """
    date_col = detect_date_column(df)
    numeric_cols = detect_numeric_columns(df)

    summary = {
        "rows": len(df),
        "columns": list(df.columns),
        "numeric_columns": numeric_cols,
        "date_column": date_col,
    }

    if date_col:
        dates = pd.to_datetime(df[date_col])
        summary["date_range"] = {
            "start": dates.min().strftime("%Y-%m-%d"),
            "end": dates.max().strftime("%Y-%m-%d"),
        }

    for col in numeric_cols:
        summary[f"{col}_stats"] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
        }

    return summary


def list_available_datasets(data_dir: str) -> List[Dict]:
    """
    List all CSV files in the data directory.

    Args:
        data_dir: Path to the data directory.

    Returns:
        List of dictionaries with file name and path.
    """
    datasets = []
    if not os.path.exists(data_dir):
        return datasets

    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_dir, filename)
            size_kb = os.path.getsize(filepath) / 1024
            datasets.append({
                "name": filename,
                "path": filepath,
                "size_kb": round(size_kb, 1),
            })

    return datasets


# NOTE: pandas 2.x removed fillna(method=). Use .ffill().bfill() instead.
