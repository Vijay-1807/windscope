export interface MetricSummary {
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  normalizedMae: number | null;
  meanActual: number | null;
}

export interface IntervalRecord {
  startTime: string; // ISO 8601 UTC
  localStartTime: string; // Formatted Europe/London
  actualMw: number | null;
  forecastMw: number | null;
  publishTime: string | null; // ISO 8601 UTC
  localPublishTime: string | null;
  errorMw: number | null;
  absoluteErrorMw: number | null;
}

export interface DailySummary {
  date: string; // YYYY-MM-DD
  expectedIntervals: number; // 48
  matchedIntervals: number;
  coveragePercent: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  meanActual: number | null;
}

export interface AnalysisResponse {
  month: string;
  timezone: string;
  units: string;
  source: string;
  generatedAt: string;
  decisionCutoffDescription: string;
  expectedIntervals: number;
  matchedIntervals: number;
  missingActualIntervals: number;
  missingEligibleForecastIntervals: number;
  coveragePercent: number;
  metrics: MetricSummary;
  series: IntervalRecord[];
  daily: DailySummary[];
  warnings: string[];
}

export interface DayAnalysisResponse {
  date: string;
  timezone: string;
  units: string;
  expectedIntervals: number;
  matchedIntervals: number;
  coveragePercent: number;
  metrics: MetricSummary;
  intervals: IntervalRecord[];
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  service: string;
  timestamp: string;
}
