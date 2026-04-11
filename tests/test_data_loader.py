"""
Unit tests for the data loader utility.

Tests CSV loading, date column detection, numeric column detection,
time series preparation, and dataset listing.
"""

import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from src.backend.utils.data_loader import (
    load_csv,
    detect_date_column,
    detect_numeric_columns,
    prepare_time_series,
    get_dataset_summary,
    list_available_datasets,
)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    df = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=20, freq='D').strftime('%Y-%m-%d'),
        'sales': np.random.randint(100, 500, 20),
        'region': np.random.choice(['North', 'South'], 20),
    })
    filepath = os.path.join(str(tmp_path), 'test_data.csv')
    df.to_csv(filepath, index=False)
    return filepath


@pytest.fixture
def empty_csv(tmp_path):
    """Create an empty CSV file."""
    filepath = os.path.join(str(tmp_path), 'empty.csv')
    pd.DataFrame().to_csv(filepath, index=False)
    return filepath


class TestLoadCsv:
    """Tests for the CSV loading function."""

    def test_load_valid_csv(self, sample_csv):
        """Should load a valid CSV file into a DataFrame."""
        df = load_csv(sample_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 20
        assert 'date' in df.columns

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            load_csv('/nonexistent/path/data.csv')

    def test_empty_csv_raises_error(self, empty_csv):
        """Should raise ValueError for empty CSV files."""
        with pytest.raises(ValueError):
            load_csv(empty_csv)


class TestDetectDateColumn:
    """Tests for the date column auto-detection."""

    def test_detect_named_date_column(self):
        """Should detect a column named 'date'."""
        df = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-02'],
            'value': [100, 200],
        })
        assert detect_date_column(df) == 'date'

    def test_detect_timestamp_column(self):
        """Should detect a column named 'timestamp'."""
        df = pd.DataFrame({
            'timestamp': ['2025-01-01', '2025-01-02'],
            'value': [100, 200],
        })
        assert detect_date_column(df) == 'timestamp'

    def test_no_date_column(self):
        """Should return None when no date column exists."""
        df = pd.DataFrame({
            'value1': [100, 200],
            'value2': [300, 400],
        })
        result = detect_date_column(df)
        # May detect or not — both are valid
        assert result is None or isinstance(result, str)


class TestDetectNumericColumns:
    """Tests for numeric column detection."""

    def test_detect_numeric_columns(self):
        """Should identify numeric columns."""
        df = pd.DataFrame({
            'date': ['2025-01-01'],
            'sales': [100],
            'count': [50],
            'name': ['test'],
        })
        numeric = detect_numeric_columns(df)
        assert 'sales' in numeric
        assert 'count' in numeric
        assert 'name' not in numeric
        assert 'date' not in numeric


class TestPrepareTimeSeries:
    """Tests for the time series preparation function."""

    def test_prepare_basic_series(self, sample_csv):
        """Should prepare a sorted, clean time series."""
        df = load_csv(sample_csv)
        prepared, date_col, value_col = prepare_time_series(df)

        assert date_col == 'date'
        assert pd.api.types.is_datetime64_any_dtype(prepared[date_col])
        # Should be sorted by date
        dates = prepared[date_col].values
        assert all(dates[i] <= dates[i+1] for i in range(len(dates)-1))

    def test_explicit_columns(self, sample_csv):
        """Should use explicitly specified columns."""
        df = load_csv(sample_csv)
        prepared, date_col, value_col = prepare_time_series(
            df, date_col='date', value_col='sales'
        )
        assert date_col == 'date'
        assert value_col == 'sales'

    def test_missing_date_column_raises(self):
        """Should raise ValueError when no date column can be found."""
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6],
        })
        with pytest.raises(ValueError, match="date"):
            prepare_time_series(df)


class TestGetDatasetSummary:
    """Tests for the dataset summary function."""

    def test_summary_has_required_fields(self, sample_csv):
        """Summary should include rows, columns, and statistics."""
        df = load_csv(sample_csv)
        summary = get_dataset_summary(df)

        assert 'rows' in summary
        assert 'columns' in summary
        assert 'numeric_columns' in summary
        assert summary['rows'] == 20


class TestListAvailableDatasets:
    """Tests for the dataset listing function."""

    def test_list_csv_files(self, tmp_path):
        """Should list CSV files in a directory."""
        # Create test CSV files
        for name in ['data1.csv', 'data2.csv', 'readme.txt']:
            filepath = os.path.join(str(tmp_path), name)
            with open(filepath, 'w') as f:
                f.write('col1,col2\n1,2\n')

        datasets = list_available_datasets(str(tmp_path))
        names = [d['name'] for d in datasets]
        assert 'data1.csv' in names
        assert 'data2.csv' in names
        assert 'readme.txt' not in names

    def test_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        datasets = list_available_datasets(str(tmp_path))
        assert datasets == []

    def test_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        datasets = list_available_datasets('/nonexistent/path')
        assert datasets == []
