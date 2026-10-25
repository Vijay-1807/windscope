import type { AnalysisResponse, DayAnalysisResponse, HealthResponse } from '../types/api';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function fetchAnalysis(
  month: string = '2026-01',
  refresh: boolean = false,
  signal?: AbortSignal
): Promise<AnalysisResponse> {
  const url = `${API_BASE}/api/analysis?month=${encodeURIComponent(month)}${refresh ? '&refresh=true' : ''}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal,
  });

  if (!response.ok) {
    let detail = `Server responded with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) detail = errJson.detail;
    } catch {
      // ignore
    }
    throw new ApiError(detail, response.status);
  }

  const data = await response.json();
  if (!data || typeof data !== 'object' || !Array.isArray(data.series)) {
    throw new ApiError('Received invalid data structure from analysis API');
  }

  return data as AnalysisResponse;
}

export async function fetchDayAnalysis(
  date: string,
  signal?: AbortSignal
): Promise<DayAnalysisResponse> {
  const url = `${API_BASE}/api/analysis/day?date=${encodeURIComponent(date)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal,
  });

  if (!response.ok) {
    let detail = `Server responded with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) detail = errJson.detail;
    } catch {
      // ignore
    }
    throw new ApiError(detail, response.status);
  }

  const data = await response.json();
  if (!data || typeof data !== 'object' || !Array.isArray(data.intervals)) {
    throw new ApiError('Received invalid data structure from daily analysis API');
  }

  return data as DayAnalysisResponse;
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const url = `${API_BASE}/api/health`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    signal,
  });

  if (!response.ok) {
    throw new ApiError(`Health check failed with status ${response.status}`, response.status);
  }

  return response.json();
}
