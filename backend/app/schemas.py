from typing import List, Optional
from pydantic import BaseModel, Field

class MetricSummary(BaseModel):
    mae: Optional[float] = Field(None, description="Mean Absolute Error in MW")
    rmse: Optional[float] = Field(None, description="Root Mean Square Error in MW")
    bias: Optional[float] = Field(None, description="Mean Error (Forecast - Actual) in MW")
    normalizedMae: Optional[float] = Field(None, description="Normalized MAE as % of mean actual generation")
    meanActual: Optional[float] = Field(None, description="Average actual generation in MW for valid intervals")

class IntervalRecord(BaseModel):
    startTime: str = Field(..., description="Target delivery start timestamp in UTC (ISO 8601)")
    localStartTime: str = Field(..., description="Target delivery start formatted in Europe/London")
    actualMw: Optional[float] = Field(None, description="Recorded actual wind generation in MW")
    forecastMw: Optional[float] = Field(None, description="Selected day-ahead forecast generation in MW")
    publishTime: Optional[str] = Field(None, description="Publication timestamp of selected forecast in UTC (ISO 8601)")
    localPublishTime: Optional[str] = Field(None, description="Publication timestamp of selected forecast in Europe/London")
    errorMw: Optional[float] = Field(None, description="Signed error in MW (forecast - actual)")
    absoluteErrorMw: Optional[float] = Field(None, description="Absolute error in MW (|forecast - actual|)")

class DailySummary(BaseModel):
    date: str = Field(..., description="Delivery date (YYYY-MM-DD) in Europe/London")
    expectedIntervals: int = Field(48, description="Expected half-hour intervals in a full day (48)")
    matchedIntervals: int = Field(..., description="Number of intervals with both valid actual and eligible forecast")
    coveragePercent: float = Field(..., description="Percentage of day intervals successfully matched")
    mae: Optional[float] = Field(None, description="Daily Mean Absolute Error in MW")
    rmse: Optional[float] = Field(None, description="Daily Root Mean Square Error in MW")
    bias: Optional[float] = Field(None, description="Daily Bias (mean forecast - actual) in MW")
    meanActual: Optional[float] = Field(None, description="Daily average actual generation in MW")

class AnalysisResponse(BaseModel):
    month: str = Field("2026-01", description="Analyzed delivery month (YYYY-MM)")
    timezone: str = Field("Europe/London", description="Reference local timezone")
    units: str = Field("MW", description="Generation and error units")
    source: str = Field("Elexon BMRS (FUELHH fuelType=WIND, WINDFOR stream)", description="Data sources utilized")
    generatedAt: str = Field(..., description="Timestamp of analysis generation (UTC ISO 8601)")
    decisionCutoffDescription: str = Field(
        ...,
        description="Formal description of the day-ahead decision cut-off policy modeled"
    )
    expectedIntervals: int = Field(1488, description="Total expected half-hourly target intervals for January (31 x 48)")
    matchedIntervals: int = Field(..., description="Number of intervals with matched actuals and eligible forecasts")
    missingActualIntervals: int = Field(..., description="Number of intervals missing actual wind generation")
    missingEligibleForecastIntervals: int = Field(..., description="Number of intervals missing an eligible forecast before cut-off")
    coveragePercent: float = Field(..., description="Coverage percentage of matched vs expected intervals")
    metrics: MetricSummary = Field(..., description="Calculated error metrics across matched intervals")
    series: List[IntervalRecord] = Field(..., description="Half-hourly series of target intervals for the month")
    daily: List[DailySummary] = Field(..., description="Daily aggregate statistics")
    warnings: List[str] = Field(default_factory=list, description="Data quality, resolution, or coverage notices")

class DayAnalysisResponse(BaseModel):
    date: str = Field(..., description="Delivery date (YYYY-MM-DD) in Europe/London")
    timezone: str = Field("Europe/London", description="Reference local timezone")
    units: str = Field("MW", description="Generation and error units")
    expectedIntervals: int = Field(48, description="Expected intervals in delivery day (48)")
    matchedIntervals: int = Field(..., description="Number of intervals with both valid actual and eligible forecast")
    coveragePercent: float = Field(..., description="Day coverage percentage")
    metrics: MetricSummary = Field(..., description="Day error metrics")
    intervals: List[IntervalRecord] = Field(..., description="Half-hourly intervals for the day")
    warnings: List[str] = Field(default_factory=list, description="Day-specific warnings")

class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Service health status")
    version: str = Field("1.0.0", description="Backend service version")
    service: str = Field("windscope-backend", description="Service identifier")
    timestamp: str = Field(..., description="Current server time (UTC ISO 8601)")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message explanation")
