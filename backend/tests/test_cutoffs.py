import pytest
from datetime import datetime, timezone
import zoneinfo
from app.services.analysis import (
    AnalysisService,
    compute_decision_deadline,
    parse_iso_datetime,
    format_utc_iso,
    format_london_display
)

LONDON_TZ = zoneinfo.ZoneInfo("Europe/London")

def test_cutoff_calculation_delivery_date():
    """Verify that the decision cut-off deadline is strictly the midnight start of the delivery date in London time."""
    # Target: 2026-01-15 14:30 London time
    target = datetime(2026, 1, 15, 14, 30, tzinfo=LONDON_TZ)
    deadline = compute_decision_deadline(target)

    # In January (GMT), 00:00:00 London is 00:00:00 UTC
    expected = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert deadline == expected

def test_strictly_before_cutoff_rule():
    """
    Test requirement 1 & 2:
    - Forecast published strictly before deadline (< deadline) is eligible.
    - Forecast published exactly at deadline (00:00:00) is EXCLUDED.
    - Forecast published after deadline is EXCLUDED.
    """
    service = AnalysisService()
    target_st = "2026-01-05T12:00:00Z"

    # Deadline for 2026-01-05 is 2026-01-05T00:00:00Z
    # 1. One second before cutoff: 2026-01-04T23:59:59Z -> ELIGIBLE
    # 2. Exactly at cutoff: 2026-01-05T00:00:00Z -> INELIGIBLE (publishTime < deadline is strict)
    # 3. After cutoff: 2026-01-05T06:00:00Z -> INELIGIBLE
    wind_records = [
        {"startTime": target_st, "publishTime": "2026-01-04T23:59:59Z", "generation": 12000},
        {"startTime": target_st, "publishTime": "2026-01-05T00:00:00Z", "generation": 13000},
        {"startTime": target_st, "publishTime": "2026-01-05T06:00:00Z", "generation": 14000},
    ]
    fuel_records = [
        {"startTime": target_st, "fuelType": "WIND", "generation": 11500}
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    matching_interval = next(s for s in analysis.series if s.startTime == target_st)

    # Must select 12000 MW published at 2026-01-04T23:59:59Z
    assert matching_interval.forecastMw == 12000
    assert matching_interval.publishTime == "2026-01-04T23:59:59Z"
    assert matching_interval.actualMw == 11500
    assert matching_interval.errorMw == 500  # 12000 - 11500

def test_closer_ineligible_forecast_is_never_used():
    """
    Test requirement 3:
    A later-published but ineligible forecast is never used even if it is closer to actual generation.
    """
    service = AnalysisService()
    target_st = "2026-01-10T15:00:00Z"
    actual_gen = 10000

    # Dec 9 22:00: Forecast = 15000 (eligible, miss = 5000)
    # Dec 10 14:00: Forecast = 10050 (ineligible, closer to actual 10000, miss = only 50)
    wind_records = [
        {"startTime": target_st, "publishTime": "2026-01-09T22:00:00Z", "generation": 15000},
        {"startTime": target_st, "publishTime": "2026-01-10T14:00:00Z", "generation": 10050},
    ]
    fuel_records = [
        {"startTime": target_st, "fuelType": "WIND", "generation": actual_gen}
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    record = next(s for s in analysis.series if s.startTime == target_st)

    assert record.forecastMw == 15000
    assert record.publishTime == "2026-01-09T22:00:00Z"

def test_multiple_eligible_versions_selects_latest():
    """
    Test requirement 4:
    The same target with multiple eligible versions selects the highest eligible publishTime.
    """
    service = AnalysisService()
    target_st = "2026-01-12T18:00:00Z"

    wind_records = [
        {"startTime": target_st, "publishTime": "2026-01-10T10:00:00Z", "generation": 8000},
        {"startTime": target_st, "publishTime": "2026-01-11T12:00:00Z", "generation": 9000},
        {"startTime": target_st, "publishTime": "2026-01-11T21:30:00Z", "generation": 9500},
    ]
    fuel_records = [
        {"startTime": target_st, "fuelType": "WIND", "generation": 9200}
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    record = next(s for s in analysis.series if s.startTime == target_st)

    assert record.forecastMw == 9500
    assert record.publishTime == "2026-01-11T21:30:00Z"

def test_joining_on_normalized_start_time():
    """
    Test requirement 5:
    Joining uses normalized target startTime, not publication timestamp or record order.
    """
    service = AnalysisService()
    t1 = "2026-01-03T10:00:00Z"
    t2 = "2026-01-03T11:00:00Z"

    # Reverse order in input lists
    wind_records = [
        {"startTime": t2, "publishTime": "2026-01-02T15:00:00Z", "generation": 11000},
        {"startTime": t1, "publishTime": "2026-01-02T15:00:00Z", "generation": 7000},
    ]
    fuel_records = [
        {"startTime": t1, "fuelType": "WIND", "generation": 7100},
        {"startTime": t2, "fuelType": "WIND", "generation": 10900},
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    r1 = next(s for s in analysis.series if s.startTime == t1)
    r2 = next(s for s in analysis.series if s.startTime == t2)

    assert r1.actualMw == 7100
    assert r1.forecastMw == 7000
    assert r1.errorMw == -100

    assert r2.actualMw == 10900
    assert r2.forecastMw == 11000
    assert r2.errorMw == 100

def test_january_1_uses_december_31_publications():
    """
    Test requirement 6:
    January 1 targets can use eligible forecast publications from December 31.
    """
    service = AnalysisService()
    target_st = "2026-01-01T04:00:00Z"

    wind_records = [
        {"startTime": target_st, "publishTime": "2025-12-31T18:00:00Z", "generation": 16000},
        {"startTime": target_st, "publishTime": "2026-01-01T02:00:00Z", "generation": 17000},  # Ineligible
    ]
    fuel_records = [
        {"startTime": target_st, "fuelType": "WIND", "generation": 15800}
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    record = next(s for s in analysis.series if s.startTime == target_st)

    assert record.forecastMw == 16000
    assert record.publishTime == "2025-12-31T18:00:00Z"
    assert record.errorMw == 200

def test_february_intervals_excluded_january_included():
    """
    Test requirement 7:
    February target intervals are excluded; January target intervals are included.
    """
    service = AnalysisService()
    jan_target = "2026-01-31T23:30:00Z"
    feb_target = "2026-02-01T00:00:00Z"

    wind_records = [
        {"startTime": jan_target, "publishTime": "2026-01-30T12:00:00Z", "generation": 5000},
        {"startTime": feb_target, "publishTime": "2026-01-31T12:00:00Z", "generation": 6000},
    ]
    fuel_records = [
        {"startTime": jan_target, "fuelType": "WIND", "generation": 4900},
        {"startTime": feb_target, "fuelType": "WIND", "generation": 5900},
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)

    # Series must strictly have 1488 expected half-hour intervals
    assert len(analysis.series) == 1488
    # Jan 31 23:30 is in series
    assert any(s.startTime == jan_target for s in analysis.series)
    # Feb 1 00:00 is NOT in series
    assert not any(s.startTime == feb_target for s in analysis.series)

def test_timestamp_offsets_normalized_safely():
    """
    Test requirement 8:
    Timestamps with Z / +00:00 / offsets are safely normalized.
    """
    dt_z = parse_iso_datetime("2026-01-15T12:00:00Z")
    dt_plus0 = parse_iso_datetime("2026-01-15T12:00:00+00:00")
    dt_offset = parse_iso_datetime("2026-01-15T14:00:00+02:00")

    assert dt_z == dt_plus0
    assert dt_z == dt_offset
    assert format_utc_iso(dt_offset) == "2026-01-15T12:00:00Z"

def test_duplicate_records_do_not_multiply_rows():
    """
    Test requirement 9 & 14:
    Duplicate records do not multiply joined interval rows. Total series length remains exactly 1,488.
    """
    service = AnalysisService()
    target_st = "2026-01-08T12:00:00Z"

    # Duplicates in wind and fuel
    wind_records = [
        {"startTime": target_st, "publishTime": "2026-01-07T12:00:00Z", "generation": 10000},
        {"startTime": target_st, "publishTime": "2026-01-07T12:00:00Z", "generation": 10000},
    ]
    fuel_records = [
        {"startTime": target_st, "fuelType": "WIND", "generation": 9800},
        {"startTime": target_st, "fuelType": "WIND", "generation": 9800},
    ]

    analysis = service.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
    assert len(analysis.series) == 1488
    matched_for_target = [s for s in analysis.series if s.startTime == target_st]
    assert len(matched_for_target) == 1
    assert matched_for_target[0].forecastMw == 10000
    assert matched_for_target[0].actualMw == 9800
