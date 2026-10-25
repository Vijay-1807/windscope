import math
import pytest
from app.services.analysis import AnalysisService

def test_hand_calculated_metric_fixture():
    """
    Test requirement 12:
    MAE, RMSE, bias, normalized MAE, and interval counts match a small hand-calculated fixture.

    Fixture:
    Interval 1: forecast=100, actual=80  -> err = +20, abs_err = 20, sq_err = 400
    Interval 2: forecast=200, actual=230 -> err = -30, abs_err = 30, sq_err = 900
    Interval 3: forecast=150, actual=150 -> err = 0,   abs_err = 0,  sq_err = 0
    Interval 4: forecast=0,   actual=0   -> err = 0,   abs_err = 0,  sq_err = 0 (Requirement 11: 0 MW is valid)

    Matched count = 4
    MAE = (20 + 30 + 0 + 0) / 4 = 12.50 MW
    RMSE = sqrt((400 + 900 + 0 + 0) / 4) = sqrt(325) = 18.03 MW
    Bias = (+20 - 30 + 0 + 0) / 4 = -2.50 MW
    Mean Actual = (80 + 230 + 150 + 0) / 4 = 115.00 MW
    Normalized MAE = (12.50 / 115.00) * 100 = 10.87%
    """
    service = AnalysisService()

    t1 = "2026-01-01T00:00:00Z"
    t2 = "2026-01-01T01:00:00Z"
    t3 = "2026-01-01T02:00:00Z"
    t4 = "2026-01-01T03:00:00Z"

    wind_records = [
        {"startTime": t1, "publishTime": "2025-12-31T12:00:00Z", "generation": 100},
        {"startTime": t2, "publishTime": "2025-12-31T12:00:00Z", "generation": 200},
        {"startTime": t3, "publishTime": "2025-12-31T12:00:00Z", "generation": 150},
        {"startTime": t4, "publishTime": "2025-12-31T12:00:00Z", "generation": 0},
    ]
    fuel_records = [
        {"startTime": t1, "fuelType": "WIND", "generation": 80},
        {"startTime": t2, "fuelType": "WIND", "generation": 230},
        {"startTime": t3, "fuelType": "WIND", "generation": 150},
        {"startTime": t4, "fuelType": "WIND", "generation": 0},
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)

    assert analysis.matchedIntervals == 4
    assert analysis.metrics.mae == 12.50
    assert analysis.metrics.rmse == 18.03
    assert analysis.metrics.bias == -2.50
    assert analysis.metrics.meanActual == 115.00
    assert analysis.metrics.normalizedMae == 10.87

def test_missing_records_not_replaced_with_zero():
    """
    Test requirement 10:
    Missing forecast and missing actual records affect coverage but do not become zero values.
    """
    service = AnalysisService()

    t_matched = "2026-01-02T10:00:00Z"
    t_actual_only = "2026-01-02T10:30:00Z"
    t_forecast_only = "2026-01-02T11:00:00Z"

    wind_records = [
        {"startTime": t_matched, "publishTime": "2026-01-01T12:00:00Z", "generation": 5000},
        {"startTime": t_forecast_only, "publishTime": "2026-01-01T12:00:00Z", "generation": 6000},
    ]
    fuel_records = [
        {"startTime": t_matched, "fuelType": "WIND", "generation": 4800},
        {"startTime": t_actual_only, "fuelType": "WIND", "generation": 4700},
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)

    # Check the intervals
    matched_row = next(s for s in analysis.series if s.startTime == t_matched)
    actual_only_row = next(s for s in analysis.series if s.startTime == t_actual_only)
    forecast_only_row = next(s for s in analysis.series if s.startTime == t_forecast_only)

    assert matched_row.actualMw == 4800
    assert matched_row.forecastMw == 5000
    assert matched_row.errorMw == 200

    # Actual only interval MUST have forecastMw=None, errorMw=None (NOT 0!)
    assert actual_only_row.actualMw == 4700
    assert actual_only_row.forecastMw is None
    assert actual_only_row.errorMw is None
    assert actual_only_row.absoluteErrorMw is None

    # Forecast only interval MUST have actualMw=None, errorMw=None (NOT 0!)
    assert forecast_only_row.forecastMw == 6000
    assert forecast_only_row.actualMw is None
    assert forecast_only_row.errorMw is None
    assert forecast_only_row.absoluteErrorMw is None

    # Only the matched row is used in metrics calculation
    assert analysis.matchedIntervals == 1
    assert analysis.metrics.mae == 200.0
    assert analysis.metrics.rmse == 200.0
    assert analysis.metrics.bias == 200.0

def test_expected_count_is_1488_and_coverage_bounds():
    """
    Test requirement 14:
    Expected count for January 2026 is exactly 1,488.
    Matched coverage cannot exceed expected count.
    """
    service = AnalysisService()
    analysis = service.build_monthly_analysis([], [], year=2026, month=1)

    assert analysis.expectedIntervals == 1488
    assert len(analysis.series) == 1488
    assert len(analysis.daily) == 31
    assert analysis.matchedIntervals == 0
    assert analysis.coveragePercent == 0.0
    assert analysis.metrics.mae is None
    assert analysis.metrics.rmse is None
