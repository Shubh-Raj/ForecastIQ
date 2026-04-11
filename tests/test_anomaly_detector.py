"""
Unit tests for the anomaly detection service.

Tests Z-score, IQR, and residual-based anomaly detection methods,
severity scoring, and context computation.
"""

import pytest
import numpy as np
import pandas as pd
from src.backend.services.anomaly_detector import (
    detect_anomalies,
    _zscore_detection,
    _iqr_detection,
    _merge_anomalies,
)


@pytest.fixture
def normal_series():
    """Create a normal series with no outliers."""
    np.random.seed(42)
    values = pd.Series(np.random.normal(100, 5, 50))
    dates = pd.Series(pd.date_range('2025-01-01', periods=50, freq='W'))
    return values, dates


@pytest.fixture
def series_with_anomalies():
    """Create a series with injected anomalies."""
    np.random.seed(42)
    values = np.random.normal(100, 5, 50)
    values[10] = 200  # Extreme spike
    values[30] = 20   # Extreme dip
    values[45] = 150  # Moderate spike
    series = pd.Series(values)
    dates = pd.Series(pd.date_range('2025-01-01', periods=50, freq='W'))
    return series, dates


class TestDetectAnomalies:
    """Tests for the main anomaly detection function."""

    def test_detects_injected_anomalies(self, series_with_anomalies):
        """Should detect the extreme spike and dip."""
        series, dates = series_with_anomalies
        result = detect_anomalies(series, dates, sensitivity=3)

        assert result['total_anomalies'] > 0
        anomaly_indices = [a['index'] for a in result['anomalies']]
        # Should catch at least the extreme spike at index 10
        assert 10 in anomaly_indices

    def test_no_anomalies_in_clean_data(self, normal_series):
        """Clean data with low sensitivity should have few/no anomalies."""
        series, dates = normal_series
        result = detect_anomalies(series, dates, sensitivity=1)
        # With very low sensitivity, should find very few anomalies
        assert result['total_anomalies'] <= 3

    def test_higher_sensitivity_finds_more(self, series_with_anomalies):
        """Higher sensitivity should detect more anomalies."""
        series, dates = series_with_anomalies
        result_low = detect_anomalies(series, dates, sensitivity=1)
        result_high = detect_anomalies(series, dates, sensitivity=5)
        assert result_high['total_anomalies'] >= result_low['total_anomalies']

    def test_anomaly_has_required_fields(self, series_with_anomalies):
        """Each anomaly should have all required fields."""
        series, dates = series_with_anomalies
        result = detect_anomalies(series, dates, sensitivity=3)

        if result['anomalies']:
            anomaly = result['anomalies'][0]
            assert 'index' in anomaly
            assert 'date' in anomaly
            assert 'value' in anomaly
            assert 'severity' in anomaly
            assert 'direction' in anomaly
            assert 'deviation_pct' in anomaly

    def test_severity_is_valid(self, series_with_anomalies):
        """Severity should be either 'critical' or 'warning'."""
        series, dates = series_with_anomalies
        result = detect_anomalies(series, dates, sensitivity=3)

        for anomaly in result['anomalies']:
            assert anomaly['severity'] in ('critical', 'warning', 'info')

    def test_summary_is_present(self, series_with_anomalies):
        """Result should include a summary section."""
        series, dates = series_with_anomalies
        result = detect_anomalies(series, dates, sensitivity=3)

        assert 'summary' in result
        assert 'total_points' in result['summary']
        assert 'anomaly_rate' in result['summary']
        assert 'critical_count' in result['summary']


class TestZscoreDetection:
    """Tests for the Z-score detection method."""

    def test_detects_extreme_values(self):
        """Should detect values far from the mean."""
        series = pd.Series([100] * 50)
        series.iloc[25] = 500  # 4+ standard deviations away
        anomalies = _zscore_detection(series, sensitivity=3)
        indices = [a[0] for a in anomalies]
        assert 25 in indices

    def test_zero_std_returns_empty(self):
        """Should return empty list when all values are identical."""
        series = pd.Series([100] * 50)
        anomalies = _zscore_detection(series, sensitivity=3)
        assert len(anomalies) == 0


class TestIqrDetection:
    """Tests for the IQR detection method."""

    def test_detects_outliers(self):
        """Should detect values outside the IQR fence."""
        np.random.seed(42)
        series = pd.Series(np.random.normal(100, 5, 50))
        series.iloc[25] = 300  # Far beyond Q3 + multiplier * IQR
        anomalies = _iqr_detection(series, sensitivity=3)
        indices = [a[0] for a in anomalies]
        assert 25 in indices


class TestMergeAnomalies:
    """Tests for the anomaly merging function."""

    def test_merge_same_index_different_methods(self):
        """Should merge anomalies at the same index."""
        anomalies = [
            (5, 'warning', 'zscore'),
            (5, 'critical', 'iqr'),
            (10, 'warning', 'zscore'),
        ]
        merged = _merge_anomalies(anomalies)
        # Index 5 should appear once with highest severity
        idx_5 = [m for m in merged if m[0] == 5]
        assert len(idx_5) == 1
        assert idx_5[0][1] == 'critical'

    def test_preserves_unique_anomalies(self):
        """Should keep anomalies at different indices."""
        anomalies = [
            (5, 'warning', 'zscore'),
            (10, 'critical', 'iqr'),
        ]
        merged = _merge_anomalies(anomalies)
        assert len(merged) == 2
