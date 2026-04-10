#!/usr/bin/env python3
"""
Generate realistic sample datasets for the AI Predictive Forecasting tool.
Creates time-series CSV files with trends, seasonality, and occasional anomalies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_weekly_sales_data(
    start_date: str = "2025-01-06",
    num_weeks: int = 52,
    base_value: float = 10000,
    trend_rate: float = 0.005,
    seasonal_amplitude: float = 2000,
    noise_std: float = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic weekly sales data with trend, seasonality, and noise.

    Args:
        start_date: First date of the time series.
        num_weeks: Number of weekly data points.
        base_value: Starting sales value.
        trend_rate: Weekly growth rate (fractional).
        seasonal_amplitude: Peak deviation due to seasonality.
        noise_std: Standard deviation of random noise.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, sales, region.
    """
    np.random.seed(seed)
    dates = pd.date_range(start=start_date, periods=num_weeks, freq="W-MON")

    trend = base_value * (1 + trend_rate) ** np.arange(num_weeks)
    seasonal = seasonal_amplitude * np.sin(2 * np.pi * np.arange(num_weeks) / 52)
    noise = np.random.normal(0, noise_std, num_weeks)

    sales = trend + seasonal + noise
    # Inject a couple of anomalies
    sales[20] *= 1.35  # Unexpected spike
    sales[38] *= 0.65  # Unexpected dip

    regions = np.random.choice(["North", "South", "East", "West"], size=num_weeks)

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "sales": np.round(sales, 2),
        "region": regions,
    })


def generate_daily_traffic_data(
    start_date: str = "2025-01-01",
    num_days: int = 180,
    base_value: float = 5000,
    seed: int = 123,
) -> pd.DataFrame:
    """
    Generate synthetic daily web traffic data.

    Args:
        start_date: First date of the time series.
        num_days: Number of daily data points.
        base_value: Average daily sessions.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, sessions, bounce_rate, avg_duration.
    """
    np.random.seed(seed)
    dates = pd.date_range(start=start_date, periods=num_days, freq="D")

    # Day-of-week effect: weekends have lower traffic
    day_of_week = dates.dayofweek
    dow_factor = np.where(day_of_week >= 5, 0.6, 1.0)

    trend = np.linspace(1.0, 1.15, num_days)
    seasonal = 500 * np.sin(2 * np.pi * np.arange(num_days) / 30)
    noise = np.random.normal(0, 300, num_days)

    sessions = (base_value * dow_factor * trend + seasonal + noise).astype(int)
    sessions = np.maximum(sessions, 100)

    # Inject anomalies
    sessions[45] = int(sessions[45] * 2.5)  # Traffic spike
    sessions[120] = int(sessions[120] * 0.3)  # Outage-like drop

    bounce_rate = np.clip(
        0.45 + np.random.normal(0, 0.05, num_days) - 0.0003 * np.arange(num_days),
        0.15, 0.85
    )
    avg_duration = np.clip(
        120 + np.random.normal(0, 20, num_days) + 0.1 * np.arange(num_days),
        30, 300
    )

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "sessions": sessions,
        "bounce_rate": np.round(bounce_rate, 3),
        "avg_duration_seconds": np.round(avg_duration, 1),
    })


def generate_monthly_usage_data(
    start_date: str = "2023-01-01",
    num_months: int = 36,
    base_value: float = 50000,
    seed: int = 456,
) -> pd.DataFrame:
    """
    Generate synthetic monthly platform usage data (active users).

    Args:
        start_date: First date of the time series.
        num_months: Number of monthly data points.
        base_value: Starting user count.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, active_users, churn_rate, new_signups.
    """
    np.random.seed(seed)
    dates = pd.date_range(start=start_date, periods=num_months, freq="MS")

    growth = base_value * (1.02) ** np.arange(num_months)
    seasonal = 3000 * np.sin(2 * np.pi * np.arange(num_months) / 12)
    noise = np.random.normal(0, 1500, num_months)

    active_users = (growth + seasonal + noise).astype(int)
    active_users[24] = int(active_users[24] * 0.7)  # Churn spike

    churn_rate = np.clip(
        0.035 + np.random.normal(0, 0.005, num_months),
        0.01, 0.10
    )
    churn_rate[24] = 0.089  # Matches the dip

    new_signups = (active_users * np.clip(
        0.08 + np.random.normal(0, 0.01, num_months),
        0.03, 0.15
    )).astype(int)

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "active_users": active_users,
        "churn_rate": np.round(churn_rate, 4),
        "new_signups": new_signups,
    })


def main():
    """Generate all sample datasets and save to data/ directory."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Generate sales data
    sales_df = generate_weekly_sales_data()
    sales_path = os.path.join(data_dir, "sample_sales.csv")
    sales_df.to_csv(sales_path, index=False)
    print(f"Generated {sales_path} ({len(sales_df)} rows)")

    # Generate traffic data
    traffic_df = generate_daily_traffic_data()
    traffic_path = os.path.join(data_dir, "sample_traffic.csv")
    traffic_df.to_csv(traffic_path, index=False)
    print(f"Generated {traffic_path} ({len(traffic_df)} rows)")

    # Generate usage data
    usage_df = generate_monthly_usage_data()
    usage_path = os.path.join(data_dir, "sample_usage.csv")
    usage_df.to_csv(usage_path, index=False)
    print(f"Generated {usage_path} ({len(usage_df)} rows)")


if __name__ == "__main__":
    main()
