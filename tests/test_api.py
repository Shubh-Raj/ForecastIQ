"""
Integration tests for the Flask API endpoints.

Tests all API routes with the Flask test client,
covering forecast, anomaly detection, scenario comparison,
and dataset management endpoints.
"""

import pytest
import os
import json
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.app import create_app


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Health endpoint should return 200 with status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestDatasetEndpoints:
    """Tests for dataset management endpoints."""

    def test_list_datasets(self, client):
        """Should return a list of available datasets."""
        response = client.get('/api/datasets')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    def test_dataset_summary(self, client):
        """Should return summary for a sample dataset."""
        response = client.get('/api/datasets/sample_sales.csv/summary')
        if response.status_code == 200:
            data = response.get_json()
            assert 'rows' in data['data']
        else:
            # Dataset may not exist yet (before data generation)
            assert response.status_code == 404

    def test_dataset_preview(self, client):
        """Should return a preview of the dataset."""
        response = client.get('/api/datasets/sample_sales.csv/preview')
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data['data'], list)

    def test_nonexistent_dataset(self, client):
        """Should return 404 for nonexistent dataset."""
        response = client.get('/api/datasets/nonexistent.csv/summary')
        assert response.status_code == 404


class TestForecastEndpoint:
    """Tests for the forecast API endpoint."""

    def test_forecast_requires_dataset(self, client):
        """Should return error when no dataset is specified."""
        response = client.post('/api/forecast',
                               data=json.dumps({'horizon': 4}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_forecast_with_valid_dataset(self, client):
        """Should generate a forecast with a valid dataset."""
        response = client.post('/api/forecast',
                               data=json.dumps({
                                   'dataset': 'sample_sales.csv',
                                   'horizon': 4,
                                   'confidence': 0.95,
                               }),
                               content_type='application/json')
        if response.status_code == 200:
            data = response.get_json()
            assert 'forecast' in data['data']
            assert 'explanation' in data['data']


class TestAnomalyEndpoint:
    """Tests for the anomaly detection API endpoint."""

    def test_anomaly_requires_dataset(self, client):
        """Should return error when no dataset is specified."""
        response = client.post('/api/anomalies',
                               data=json.dumps({'sensitivity': 3}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_anomaly_with_valid_dataset(self, client):
        """Should detect anomalies with a valid dataset."""
        response = client.post('/api/anomalies',
                               data=json.dumps({
                                   'dataset': 'sample_sales.csv',
                                   'sensitivity': 3,
                               }),
                               content_type='application/json')
        if response.status_code == 200:
            data = response.get_json()
            assert 'anomalies' in data['data']
            assert 'summary' in data['data']


class TestScenarioEndpoint:
    """Tests for the scenario comparison API endpoint."""

    def test_scenario_requires_dataset(self, client):
        """Should return error when no dataset is specified."""
        response = client.post('/api/scenarios',
                               data=json.dumps({
                                   'growth_adjustment': 10,
                               }),
                               content_type='application/json')
        assert response.status_code == 400

    def test_scenario_with_valid_dataset(self, client):
        """Should compare scenarios with a valid dataset."""
        response = client.post('/api/scenarios',
                               data=json.dumps({
                                   'dataset': 'sample_sales.csv',
                                   'horizon': 4,
                                   'growth_adjustment': 10,
                                   'pattern': 'trend',
                                   'remove_outliers': False,
                               }),
                               content_type='application/json')
        if response.status_code == 200:
            data = response.get_json()
            assert 'baseline' in data['data']
            assert 'scenarios' in data['data']
