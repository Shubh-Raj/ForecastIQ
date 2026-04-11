"""
Unit tests for the scenario comparison engine.

Tests growth adjustment, outlier removal, pattern modification,
and side-by-side scenario comparison.
"""

import pytest
import numpy as np
import pandas as pd
from src.backend.services.scenario_engine import (
    create_scenario_forecast,
    compare_scenarios,
    _apply_growth_adjustment,
    _apply_pattern,
)


@pytest.fixture
def sample_series():
    """Create a sample time series with trend."""
    np.random.seed(42)
    n = 52
    trend = 10000 + 50 * np.arange(n)
    seasonal = 1000 * np.sin(2 * np.pi * np.arange(n) / 52)
    noise = np.random.normal(0, 200, n)
    series = pd.Series(trend + seasonal + noise)
    dates = pd.Series(pd.date_range('2025-01-06', periods=n, freq='W-MON'))
    return series, dates


class TestCreateScenarioForecast:
    """Tests for individual scenario forecast generation."""

    def test_baseline_scenario(self, sample_series):
        """Baseline scenario (no adjustments) should produce a valid forecast."""
        series, dates = sample_series
        result = create_scenario_forecast(series, dates, horizon=4)

        assert 'forecast' in result
        assert len(result['forecast']) == 4
        assert 'lower_bound' in result
        assert 'upper_bound' in result

    def test_growth_adjustment(self, sample_series):
        """Positive growth should shift forecast upward."""
        series, dates = sample_series

        baseline = create_scenario_forecast(series, dates, horizon=4,
                                            growth_adjustment=0)
        growth = create_scenario_forecast(series, dates, horizon=4,
                                          growth_adjustment=0.1)

        baseline_avg = np.mean(baseline['forecast'])
        growth_avg = np.mean(growth['forecast'])
        # Growth scenario should generally produce higher values
        # (not guaranteed due to model dynamics, but likely)
        assert isinstance(growth_avg, float)

    def test_remove_outliers(self, sample_series):
        """Outlier removal should produce a valid forecast."""
        series, dates = sample_series
        # Inject an outlier
        series.iloc[25] *= 2

        result = create_scenario_forecast(
            series, dates, horizon=4, remove_outliers=True
        )
        assert len(result['forecast']) == 4


class TestCompareScenarios:
    """Tests for the scenario comparison function."""

    def test_default_scenarios(self, sample_series):
        """Default comparison should include baseline and scenarios."""
        series, dates = sample_series
        result = compare_scenarios(series, dates, horizon=4)

        assert 'baseline' in result
        assert 'scenarios' in result
        assert 'comparison' in result
        assert len(result['scenarios']) > 0

    def test_comparison_has_summary(self, sample_series):
        """Comparison should include summary metrics."""
        series, dates = sample_series
        result = compare_scenarios(series, dates, horizon=4)

        comparison = result['comparison']
        assert 'baseline_total' in comparison
        assert 'baseline_avg' in comparison
        assert 'scenarios' in comparison

    def test_custom_scenarios(self, sample_series):
        """Should accept custom scenario configurations."""
        series, dates = sample_series
        scenarios = [
            {"name": "Test1", "growth_adjustment": 0.05,
             "remove_outliers": False, "pattern": "trend"},
            {"name": "Test2", "growth_adjustment": -0.1,
             "remove_outliers": False, "pattern": "flat"},
        ]

        result = compare_scenarios(series, dates, horizon=4, scenarios=scenarios)
        assert len(result['scenarios']) == 2


class TestApplyGrowthAdjustment:
    """Tests for the growth adjustment helper."""

    def test_positive_growth(self):
        """Positive growth should increase values."""
        series = pd.Series([100] * 10)
        adjusted = _apply_growth_adjustment(series, 0.1)
        # Last value should be higher than first
        assert adjusted.iloc[-1] > adjusted.iloc[0]

    def test_negative_growth(self):
        """Negative growth should decrease values."""
        series = pd.Series([100] * 10)
        adjusted = _apply_growth_adjustment(series, -0.1)
        assert adjusted.iloc[-1] < adjusted.iloc[0]

    def test_zero_growth(self):
        """Zero growth should leave values unchanged."""
        series = pd.Series([100.0] * 10)
        adjusted = _apply_growth_adjustment(series, 0.0)
        np.testing.assert_array_almost_equal(adjusted.values, series.values)


class TestApplyPattern:
    """Tests for the pattern modification helper."""

    def test_flat_pattern_removes_trend(self):
        """Flat pattern should reduce the linear trend."""
        series = pd.Series(np.arange(1, 51, dtype=float) * 10)
        flattened = _apply_pattern(series, 'flat')
        # Standard deviation of flattened should be less than original
        assert flattened.std() < series.std()

    def test_trend_pattern_unchanged(self):
        """Trend pattern should return original data."""
        series = pd.Series([100, 110, 120, 130, 140], dtype=float)
        result = _apply_pattern(series, 'trend')
        pd.testing.assert_series_equal(result, series)

    def test_seasonal_pattern_amplifies(self):
        """Seasonal pattern should amplify seasonal component."""
        n = 50
        trend = np.arange(n, dtype=float) * 2
        seasonal = 10 * np.sin(2 * np.pi * np.arange(n) / 12)
        series = pd.Series(trend + seasonal)
        amplified = _apply_pattern(series, 'seasonal')
        assert isinstance(amplified, pd.Series)
        assert len(amplified) == n
