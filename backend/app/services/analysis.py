import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import zoneinfo

from ..schemas import (
    AnalysisResponse,
    DayAnalysisResponse,
    MetricSummary,
    IntervalRecord,
    DailySummary,
)
from ..clients.elexon import ElexonClient

logger = logging.getLogger("windscope.analysis")

LONDON_TZ = zoneinfo.ZoneInfo("Europe/London")

DECISION_CUTOFF_DESCRIPTION = (
    "Day-Ahead Purchase Cut-off: For a target delivery interval on local delivery date D, "
    "the deadline is the start of date D in Europe/London (00:00:00 local time). "
    "Only forecasts published strictly before this deadline (publishTime < deadline) are eligible. "
    "From all eligible versions, the latest published forecast is selected."
)

def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 string safely into a timezone-aware UTC datetime."""
    # Handle 'Z' suffix
    clean_str = dt_str.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def format_utc_iso(dt: datetime) -> str:
    """Format UTC datetime as standard ISO 8601 string ending with Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def format_london_display(dt: datetime) -> str:
    """Format datetime for display in Europe/London timezone."""
    lon_dt = dt.astimezone(LONDON_TZ)
    return lon_dt.strftime("%Y-%m-%d %H:%M %Z")

def compute_decision_deadline(target_dt: datetime) -> datetime:
    """
    Calculate the day-ahead purchasing cut-off for a target delivery timestamp.
    Target is converted to Europe/London to identify delivery date D.
    The cut-off deadline is the start of date D in Europe/London (midnight local time),
    returned as a timezone-aware UTC datetime.
    """
    local_target = target_dt.astimezone(LONDON_TZ)
    local_deadline = datetime(
        local_target.year, local_target.month, local_target.day, 0, 0, 0, tzinfo=LONDON_TZ
    )
    return local_deadline.astimezone(timezone.utc)

class AnalysisService:
    """Domain service for retrieving, cleaning, joining, and analyzing wind generation and forecasts."""

    def __init__(self, client: Optional[ElexonClient] = None, cache_ttl_seconds: int = 300):
        self.client = client or ElexonClient()
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_analysis: Optional[AnalysisResponse] = None
        self._cached_at: Optional[datetime] = None
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_monthly_analysis(self, month: str = "2026-01", force_refresh: bool = False) -> AnalysisResponse:
        """Get the full monthly analysis for the requested month (currently 2026-01)."""
        if month != "2026-01":
            raise ValueError(f"Unsupported month '{month}'. Only '2026-01' is supported in this challenge.")

        async with self._get_lock():
            now = datetime.now(timezone.utc)
            if (
                not force_refresh
                and self._cached_analysis is not None
                and self._cached_at is not None
                and (now - self._cached_at).total_seconds() < self.cache_ttl_seconds
            ):
                logger.info("Serving monthly analysis from in-memory cache")
                return self._cached_analysis

            logger.info("Fetching fresh Elexon data for month %s", month)

            # Query windows:
            # FUELHH Actuals: from 2026-01-01T00:00:00Z to 2026-02-01T01:00:00Z
            fuelhh_from = "2026-01-01T00:00:00Z"
            fuelhh_to = "2026-02-01T01:00:00Z"

            # WINDFOR Forecasts: retrieve forecasts published well before Jan 1 to capture eligible Dec 31 vintages
            windfor_from = "2025-12-25T00:00:00Z"
            windfor_to = "2026-01-31T01:00:00Z"

            fuel_records, wind_records = await asyncio.gather(
                self.client.fetch_fuelhh_wind(fuelhh_from, fuelhh_to),
                self.client.fetch_windfor(windfor_from, windfor_to)
            )

            analysis = self.build_monthly_analysis(fuel_records, wind_records, year=2026, month=1)
            self._cached_analysis = analysis
            self._cached_at = now
            return analysis

    async def get_day_analysis(self, date_str: str) -> DayAnalysisResponse:
        """Get interval-level analysis for an allowed date in January 2026."""
        # Validate date format and month
        try:
            day_dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")

        if day_dt.year != 2026 or day_dt.month != 1:
            raise ValueError(f"Date '{date_str}' is outside supported analysis scope (January 2026).")

        monthly = await self.get_monthly_analysis(month="2026-01", force_refresh=False)

        # Filter intervals belonging to this delivery date in Europe/London
        day_intervals: List[IntervalRecord] = []
        for interval in monthly.series:
            st = parse_iso_datetime(interval.startTime)
            lon_dt = st.astimezone(LONDON_TZ)
            if lon_dt.strftime("%Y-%m-%d") == date_str:
                day_intervals.append(interval)

        # Find matching daily summary
        daily_summary = next((d for d in monthly.daily if d.date == date_str), None)
        matched_count = daily_summary.matchedIntervals if daily_summary else 0
        coverage = daily_summary.coveragePercent if daily_summary else 0.0

        day_metrics = MetricSummary(
            mae=daily_summary.mae if daily_summary else None,
            rmse=daily_summary.rmse if daily_summary else None,
            bias=daily_summary.bias if daily_summary else None,
            normalizedMae=(
                round((daily_summary.mae / daily_summary.meanActual) * 100, 2)
                if daily_summary and daily_summary.mae is not None and daily_summary.meanActual and daily_summary.meanActual > 0
                else None
            ),
            meanActual=daily_summary.meanActual if daily_summary else None,
        )

        day_warnings = []
        if matched_count < 48:
            day_warnings.append(
                f"Day {date_str} has {matched_count} matched intervals out of 48 expected half-hours "
                f"({coverage:.1f}% coverage) due to hourly forecast resolution in WINDFOR."
            )

        return DayAnalysisResponse(
            date=date_str,
            timezone="Europe/London",
            units="MW",
            expectedIntervals=48,
            matchedIntervals=matched_count,
            coveragePercent=coverage,
            metrics=day_metrics,
            intervals=day_intervals,
            warnings=day_warnings,
        )

    def build_monthly_analysis(
        self,
        fuel_records: List[Dict[str, Any]],
        wind_records: List[Dict[str, Any]],
        year: int = 2026,
        month: int = 1,
    ) -> AnalysisResponse:
        """
        Pure function: cleans raw records, selects decision-time vintage, joins on target startTime,
        and computes metrics for the given month.
        """
        # 1. Clean and index actuals: map normalized UTC ISO startTime -> actual generation MW
        actual_map: Dict[str, float] = {}
        for r in fuel_records:
            st_raw = r.get("startTime")
            gen = r.get("generation")
            if not st_raw or gen is None:
                continue
            try:
                st_dt = parse_iso_datetime(st_raw)
                lon_dt = st_dt.astimezone(LONDON_TZ)
                # Ensure target delivery interval is strictly within the target month
                if lon_dt.year == year and lon_dt.month == month:
                    iso_key = format_utc_iso(st_dt)
                    # Keep latest if duplicate reported
                    actual_map[iso_key] = float(gen)
            except Exception as e:
                logger.debug("Skipping malformed FUELHH actual record: %s (err: %s)", r, e)
                continue

        # 2. Clean, filter by cut-off, and group forecast candidates
        # Group by target startTime -> list of eligible (publish_dt, raw_pt_str, generation_mw)
        candidates_by_target: Dict[str, List[Tuple[datetime, str, float]]] = {}

        for r in wind_records:
            st_raw = r.get("startTime")
            pt_raw = r.get("publishTime")
            gen = r.get("generation")
            if not st_raw or not pt_raw or gen is None:
                continue
            try:
                st_dt = parse_iso_datetime(st_raw)
                lon_target = st_dt.astimezone(LONDON_TZ)
                if lon_target.year != year or lon_target.month != month:
                    # Outside target month
                    continue

                pt_dt = parse_iso_datetime(pt_raw)
                # Compute day-ahead purchase cut-off for this delivery date
                deadline_utc = compute_decision_deadline(st_dt)

                # CRITICAL RULE: publishTime < deadline (strictly before start of delivery day)
                if pt_dt < deadline_utc:
                    iso_key = format_utc_iso(st_dt)
                    if iso_key not in candidates_by_target:
                        candidates_by_target[iso_key] = []
                    candidates_by_target[iso_key].append((pt_dt, pt_raw, float(gen)))

            except Exception as e:
                logger.debug("Skipping malformed WINDFOR forecast record: %s (err: %s)", r, e)
                continue

        # 3. Select the best vintage for each target startTime
        # Rule: Greatest publishTime. Tie-break: highest generation, stable.
        selected_forecasts: Dict[str, Tuple[str, float]] = {}
        for iso_key, candidates in candidates_by_target.items():
            if candidates:
                best = max(candidates, key=lambda c: (c[0], c[2]))
                selected_forecasts[iso_key] = (best[1], best[2])

        # 4. Generate all expected half-hour intervals for the target month
        # January has 31 days * 48 half-hours = 1,488 intervals
        days_in_month = 31
        expected_intervals = days_in_month * 48
        month_start_utc = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)

        series: List[IntervalRecord] = []
        matched_records = []
        missing_actual_count = 0
        missing_forecast_count = 0

        # Build daily tracking structures
        daily_intervals: Dict[str, List[IntervalRecord]] = {}

        for i in range(expected_intervals):
            interval_dt = month_start_utc + timedelta(minutes=30 * i)
            iso_key = format_utc_iso(interval_dt)
            local_display = format_london_display(interval_dt)

            lon_dt = interval_dt.astimezone(LONDON_TZ)
            day_str = lon_dt.strftime("%Y-%m-%d")
            if day_str not in daily_intervals:
                daily_intervals[day_str] = []

            act_mw = actual_map.get(iso_key)
            fc_tuple = selected_forecasts.get(iso_key)

            if act_mw is None:
                missing_actual_count += 1
            if fc_tuple is None:
                missing_forecast_count += 1

            if act_mw is not None and fc_tuple is not None:
                fc_pt_raw, fc_mw = fc_tuple
                fc_pt_dt = parse_iso_datetime(fc_pt_raw)
                err_mw = round(fc_mw - act_mw, 2)
                abs_err_mw = round(abs(err_mw), 2)
                record = IntervalRecord(
                    startTime=iso_key,
                    localStartTime=local_display,
                    actualMw=round(act_mw, 2),
                    forecastMw=round(fc_mw, 2),
                    publishTime=format_utc_iso(fc_pt_dt),
                    localPublishTime=format_london_display(fc_pt_dt),
                    errorMw=err_mw,
                    absoluteErrorMw=abs_err_mw,
                )
                matched_records.append(record)
            else:
                fc_pt_iso = None
                fc_pt_local = None
                fc_mw = None
                if fc_tuple is not None:
                    fc_pt_raw, fc_mw = fc_tuple
                    fc_pt_dt = parse_iso_datetime(fc_pt_raw)
                    fc_pt_iso = format_utc_iso(fc_pt_dt)
                    fc_pt_local = format_london_display(fc_pt_dt)
                    fc_mw = round(fc_mw, 2)

                record = IntervalRecord(
                    startTime=iso_key,
                    localStartTime=local_display,
                    actualMw=round(act_mw, 2) if act_mw is not None else None,
                    forecastMw=fc_mw,
                    publishTime=fc_pt_iso,
                    localPublishTime=fc_pt_local,
                    errorMw=None,
                    absoluteErrorMw=None,
                )

            series.append(record)
            daily_intervals[day_str].append(record)

        # 5. Compute Month-Level Metrics across matched intervals
        matched_count = len(matched_records)
        coverage_pct = round((matched_count / expected_intervals) * 100, 2)

        if matched_count > 0:
            abs_errors = [m.absoluteErrorMw for m in matched_records if m.absoluteErrorMw is not None]
            errors = [m.errorMw for m in matched_records if m.errorMw is not None]
            actuals = [m.actualMw for m in matched_records if m.actualMw is not None]

            mae = round(sum(abs_errors) / matched_count, 2)
            rmse = round(math.sqrt(sum(e ** 2 for e in errors) / matched_count), 2)
            bias = round(sum(errors) / matched_count, 2)
            mean_actual = round(sum(actuals) / matched_count, 2)
            normalized_mae = (
                round((mae / mean_actual) * 100, 2) if mean_actual > 0 else None
            )

            metrics = MetricSummary(
                mae=mae,
                rmse=rmse,
                bias=bias,
                normalizedMae=normalized_mae,
                meanActual=mean_actual,
            )
        else:
            metrics = MetricSummary(
                mae=None,
                rmse=None,
                bias=None,
                normalizedMae=None,
                meanActual=None,
            )

        # 6. Compute Daily Summaries
        daily_summaries: List[DailySummary] = []
        for day_str in sorted(daily_intervals.keys()):
            day_records = daily_intervals[day_str]
            day_matched = [r for r in day_records if r.actualMw is not None and r.forecastMw is not None]
            d_matched_cnt = len(day_matched)
            d_coverage = round((d_matched_cnt / 48) * 100, 2)

            if d_matched_cnt > 0:
                d_abs_err = [r.absoluteErrorMw for r in day_matched if r.absoluteErrorMw is not None]
                d_err = [r.errorMw for r in day_matched if r.errorMw is not None]
                d_act = [r.actualMw for r in day_matched if r.actualMw is not None]

                d_mae = round(sum(d_abs_err) / d_matched_cnt, 2)
                d_rmse = round(math.sqrt(sum(e ** 2 for e in d_err) / d_matched_cnt), 2)
                d_bias = round(sum(d_err) / d_matched_cnt, 2)
                d_mean_act = round(sum(d_act) / d_matched_cnt, 2)
            else:
                d_mae = None
                d_rmse = None
                d_bias = None
                d_mean_act = None

            daily_summaries.append(
                DailySummary(
                    date=day_str,
                    expectedIntervals=48,
                    matchedIntervals=d_matched_cnt,
                    coveragePercent=d_coverage,
                    mae=d_mae,
                    rmse=d_rmse,
                    bias=d_bias,
                    meanActual=d_mean_act,
                )
            )

        # 7. Formulate Warnings & Transparency notices
        warnings: List[str] = []
        if missing_forecast_count > 0:
            warnings.append(
                f"Elexon WINDFOR dataset publishes national wind forecasts at hourly intervals (:00), "
                f"matching {matched_count} of {expected_intervals} half-hours ({coverage_pct}% coverage). "
                f"Non-matched (:30) intervals display recorded actuals only."
            )
        if missing_actual_count > 0:
            warnings.append(
                f"{missing_actual_count} intervals in January 2026 lack recorded actual wind generation in FUELHH."
            )

        return AnalysisResponse(
            month=f"{year:04d}-{month:02d}",
            timezone="Europe/London",
            units="MW",
            source="Elexon BMRS (FUELHH fuelType=WIND, WINDFOR stream)",
            generatedAt=format_utc_iso(datetime.now(timezone.utc)),
            decisionCutoffDescription=DECISION_CUTOFF_DESCRIPTION,
            expectedIntervals=expected_intervals,
            matchedIntervals=matched_count,
            missingActualIntervals=missing_actual_count,
            missingEligibleForecastIntervals=missing_forecast_count,
            coveragePercent=coverage_pct,
            metrics=metrics,
            series=series,
            daily=daily_summaries,
            warnings=warnings,
        )
