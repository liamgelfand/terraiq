"""
Unit tests for the optimizer physics layer.

These tests run purely in-process with synthetic data — no database,
no Celery, no external geocoding or road network calls.
"""
from __future__ import annotations

import numpy as np
import pytest

from simulation.evaluator import EvaluationReport, SimulationResult


def _make_result(fuel_liters: float, distance_km: float = 100.0) -> SimulationResult:
    """Construct a minimal SimulationResult with the given total fuel."""
    n = 10
    speeds = np.full(n, 25.0)  # 25 m/s ≈ 90 km/h
    distances = np.linspace(0, distance_km * 1000, n)
    elevations = np.zeros(n)
    grades = np.zeros(n)
    segment_fuel = np.full(n - 1, fuel_liters / (n - 1))
    segment_power = np.zeros(n - 1)

    return SimulationResult(
        route_name="test",
        total_distance_km=distance_km,
        elevation_gain_m=0.0,
        elevation_loss_m=0.0,
        total_fuel_liters=fuel_liters,
        total_fuel_kg=fuel_liters * 0.84,
        fuel_per_100km=fuel_liters / distance_km * 100,
        vehicle_name="Test Vehicle",
        speed_profile_ms=speeds,
        distances_m=distances,
        elevations_m=elevations,
        grades=grades,
        speed_limits_ms=speeds,
        segment_fuel_L=segment_fuel,
        segment_power_kw=segment_power,
        lat=np.zeros(n),
        lon=np.zeros(n),
    )


# ── EvaluationReport ──────────────────────────────────────────────────────────

def test_fuel_saved_liters_positive():
    baseline = _make_result(fuel_liters=40.0)
    optimized = _make_result(fuel_liters=34.0)
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    assert report.fuel_saved_liters == pytest.approx(6.0, abs=0.01)


def test_fuel_saved_pct_in_range():
    baseline = _make_result(fuel_liters=40.0)
    optimized = _make_result(fuel_liters=34.0)
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    # 6/40 = 15%
    assert report.fuel_saved_pct == pytest.approx(15.0, abs=0.1)


def test_cost_saved_positive():
    baseline = _make_result(fuel_liters=40.0)
    optimized = _make_result(fuel_liters=34.0)
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    assert report.cost_saved_usd > 0


def test_co2_saved_positive():
    baseline = _make_result(fuel_liters=40.0)
    optimized = _make_result(fuel_liters=34.0)
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    assert report.co2_saved_kg > 0


def test_no_savings_when_equal():
    result = _make_result(fuel_liters=40.0)
    report = EvaluationReport(baseline=result, optimized=result)
    assert report.fuel_saved_liters == pytest.approx(0.0, abs=0.001)
    assert report.fuel_saved_pct == pytest.approx(0.0, abs=0.001)


def test_fuel_per_100km_consistent():
    """fuel_per_100km should equal total_fuel / distance * 100."""
    result = _make_result(fuel_liters=40.0, distance_km=200.0)
    assert result.fuel_per_100km == pytest.approx(20.0, abs=0.01)


def test_savings_never_negative_when_optimized_uses_more_fuel():
    """
    If the optimized result somehow uses more fuel (edge case), savings
    should be negative — the report shouldn't clamp or hide the regression.
    """
    baseline = _make_result(fuel_liters=30.0)
    optimized = _make_result(fuel_liters=32.0)
    report = EvaluationReport(baseline=baseline, optimized=optimized)
    assert report.fuel_saved_liters < 0
    assert report.fuel_saved_pct < 0
