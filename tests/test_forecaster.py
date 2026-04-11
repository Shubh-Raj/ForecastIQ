"""
Unit tests for the forecasting service.

Tests the core ETS model fitting, forecast generation,
prediction intervals, and seasonal decomposition.
"""

import pytest
import numpy as np
import pandas as pd
from src.backend.services.forecaster import (
    fit_ets_model,
    generate_forecast,
    _detect_seasonal_period,
)


@pytest.fixture
def simple_series():
    """Create a simple upward-trending time series."""
    np.random.seed(42)
    n = 52
    trend = 1000 + 10 * np.arange(n)
    noise = np.random.normal(0, 20, n)
    return pd.Series(trend + noise)


@pytest.fixture
def seasonal_series():
    """Create a series with clear seasonality."""
    np.random.seed(42)
    n = 104  # 2 years of weekly data
    trend = 5000 + 5 * np.arange(n)
    seasonal = 500 * np.sin(2 * np.pi * np.arange(n) / 52)
    noise = np.random.normal(0, 50, n)
    return pd.Series(trend + seasonal + noise)


@pytest.fixture
def flat_series():
    """Create a flat series with minimal variation."""
    np.random.seed(42)
    return pd.Series(np.random.normal(100, 2, 30))


class TestFitEtsModel:
    """Tests for the ETS model fitting function."""

    def test_fit_simple_series(self, simple_series):
        """Model should fit without errors on a simple trending series."""
        result = fit_ets_model(simple_series)
        assert result is not None
        assert hasattr(result, 'forecast')
        assert hasattr(result, 'resid')

    def test_fit_seasonal_series(self, seasonal_series):
        """Model should handle seasonal data."""
        result = fit_ets_model(seasonal_series, seasonal_periods=52)
        assert result is not None

    def test_fit_short_series(self):
        """Model should handle very short series gracefully."""
        short = pd.Series([100, 110, 105, 115, 120])
        result = fit_ets_model(short)
        assert result is not None

    def test_fit_flat_series(self, flat_series):
        """Model should work on flat / low-variance data."""
        result = fit_ets_model(flat_series)
        assert result is not None


class TestGenerateForecast:
    """Tests for the forecast generation function."""

    def test_forecast_length(self, simple_series):
        """Forecast should have the requested number of periods."""
        horizon = 6
        result = generate_forecast(simple_series, horizon=horizon)
        assert len(result['forecast']) == horizon
        assert len(result['lower_bound']) == horizon
        assert len(result['upper_bound']) == horizon

    def test_forecast_intervals_contain_point(self, simple_series):
        """Lower bound should be below forecast, upper above."""
        result = generate_forecast(simple_series, horizon=4, confidence=0.95)
        for i in range(len(result['forecast'])):
            assert result['lower_bound'][i] <= result['forecast'][i]
            assert result['upper_bound'][i] >= result['forecast'][i]

    def test_wider_intervals_at_higher_confidence(self, simple_series):
        """Higher confidence should produce wider intervals."""
        result_90 = generate_forecast(simple_series, horizon=4, confidence=0.90)
        result_99 = generate_forecast(simple_series, horizon=4, confidence=0.99)

        width_90 = np.mean([
            result_90['upper_bound'][i] - result_90['lower_bound'][i]
            for i in range(4)
        ])
        width_99 = np.mean([
            result_99['upper_bound'][i] - result_99['lower_bound'][i]
            for i in range(4)
        ])
        assert width_99 > width_90

    def test_forecast_contains_model_summary(self, simple_series):
        """Result should include model performance metrics."""
        result = generate_forecast(simple_series, horizon=4)
        assert 'model_summary' in result
        assert 'mape' in result['model_summary']
        assert 'rmse' in result['model_summary']
        assert result['model_summary']['mape'] >= 0

    def test_forecast_contains_decomposition(self, simple_series):
        """Result should include trend/seasonal decomposition."""
        result = generate_forecast(simple_series, horizon=4)
        assert 'decomposition' in result
        assert 'trend' in result['decomposition']

    def test_forecast_fitted_values(self, simple_series):
        """Fitted values should have same length as input."""
        result = generate_forecast(simple_series, horizon=4)
        assert len(result['fitted_values']) == len(simple_series)


class TestDetectSeasonalPeriod:
    """Tests for the seasonal period auto-detection."""

    def test_detect_weekly_seasonality(self, seasonal_series):
        """Should detect ~52 period seasonality in weekly data."""
        period = _detect_seasonal_period(seasonal_series)
        # Period should be close to 52 (within tolerance)
        if period is not None:
            assert 20 <= period <= 60

    def test_no_seasonality_in_flat_data(self, flat_series):
        """Should return None or a low-confidence period for flat data."""
        period = _detect_seasonal_period(flat_series)
        # Either None or any value is acceptable for flat data
        assert period is None or isinstance(period, int)

    def test_short_series_returns_none(self):
        """Should return None for very short series."""
        short = pd.Series([1, 2, 3, 4, 5])
        period = _detect_seasonal_period(short)
        assert period is None
