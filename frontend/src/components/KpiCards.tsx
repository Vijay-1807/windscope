import React from 'react';
import { Target, Activity, Gauge, Database } from 'lucide-react';
import type { MetricSummary } from '../types/api';
import { formatMw, formatPercent } from '../lib/formatters';

interface KpiCardsProps {
  metrics: MetricSummary | null;
  matchedIntervals: number;
  expectedIntervals: number;
  coveragePercent: number;
}

export const KpiCards: React.FC<KpiCardsProps> = ({
  metrics,
  matchedIntervals,
  expectedIntervals,
  coveragePercent,
}) => {
  const maeVal = metrics?.mae;
  const rmseVal = metrics?.rmse;
  const biasVal = metrics?.bias;
  const nmaeVal = metrics?.normalizedMae;

  return (
    <section className="kpi-grid" aria-label="Key Performance Indicators">
      {/* 1. MAE Card */}
      <div className="kpi-card" data-testid="kpi-mae">
        <div className="kpi-header">
          <span className="kpi-label">Mean Absolute Error (MAE)</span>
          <Target size={16} className="kpi-icon" aria-hidden="true" />
        </div>
        <div className="kpi-value-container">
          <span className="kpi-value">
            {maeVal !== null && maeVal !== undefined ? formatMw(maeVal).replace(' MW', '') : '—'}
          </span>
          {maeVal !== null && maeVal !== undefined && <span className="kpi-unit">MW</span>}
        </div>
        <div className="kpi-explanation">
          {nmaeVal !== null && nmaeVal !== undefined ? (
            <span>{formatPercent(nmaeVal)} of mean generation</span>
          ) : (
            <span>Average forecast deviation</span>
          )}
        </div>
      </div>

      {/* 2. RMSE Card */}
      <div className="kpi-card" data-testid="kpi-rmse">
        <div className="kpi-header">
          <span className="kpi-label">Root Mean Square Error</span>
          <Activity size={16} className="kpi-icon" aria-hidden="true" />
        </div>
        <div className="kpi-value-container">
          <span className="kpi-value">
            {rmseVal !== null && rmseVal !== undefined ? formatMw(rmseVal).replace(' MW', '') : '—'}
          </span>
          {rmseVal !== null && rmseVal !== undefined && <span className="kpi-unit">MW</span>}
        </div>
        <div className="kpi-explanation">
          <span>Residual std dev (penalizes outliers)</span>
        </div>
      </div>

      {/* 3. Bias Card */}
      <div className="kpi-card" data-testid="kpi-bias">
        <div className="kpi-header">
          <span className="kpi-label">Mean Forecast Bias</span>
          <Gauge size={16} className="kpi-icon" aria-hidden="true" />
        </div>
        <div className="kpi-value-container">
          <span
            className="kpi-value"
            style={{
              color: biasVal && biasVal > 0 ? 'var(--forecast)' : biasVal && biasVal < 0 ? '#FB923C' : 'var(--ink)'
            }}
          >
            {biasVal !== null && biasVal !== undefined
              ? (biasVal > 0 ? `+${biasVal.toFixed(1)}` : biasVal.toFixed(1))
              : '—'}
          </span>
          {biasVal !== null && biasVal !== undefined && <span className="kpi-unit">MW</span>}
        </div>
        <div className="kpi-explanation">
          <span>
            {biasVal && biasVal > 0
              ? 'Over-forecast bias (Forecast > Actual)'
              : biasVal && biasVal < 0
              ? 'Under-forecast bias (Forecast < Actual)'
              : 'Zero net systematic bias'}
          </span>
        </div>
      </div>

      {/* 4. Coverage Card */}
      <div className="kpi-card" data-testid="kpi-coverage">
        <div className="kpi-header">
          <span className="kpi-label">Data Coverage</span>
          <Database size={16} className="kpi-icon" aria-hidden="true" />
        </div>
        <div className="kpi-value-container">
          <span className="kpi-value">{formatPercent(coveragePercent)}</span>
          <span className="kpi-unit">of month</span>
        </div>
        <div className="kpi-explanation">
          <span>
            {matchedIntervals.toLocaleString()} of {expectedIntervals.toLocaleString()} target half-hours matched
          </span>
        </div>
      </div>
    </section>
  );
};
