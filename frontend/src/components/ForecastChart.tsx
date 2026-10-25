import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { IntervalRecord } from '../types/api';
import { formatMwPlain, formatSignedMw, formatDateTime, formatHourMinute } from '../lib/formatters';

interface ForecastChartProps {
  series: IntervalRecord[];
  isSingleDay: boolean;
  selectedDate?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;

  const data: IntervalRecord = payload[0]?.payload;
  if (!data) return null;

  return (
    <div className="custom-tooltip" role="tooltip">
      <div className="tooltip-title">
        {data.localStartTime || formatDateTime(data.startTime)}
      </div>

      <div className="tooltip-row">
        <span className="tooltip-label">
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--actual)' }} />
          Actual Generation:
        </span>
        <span className="tooltip-value" style={{ color: 'var(--actual)' }}>
          {data.actualMw !== null ? `${formatMwPlain(data.actualMw)} MW` : '—'}
        </span>
      </div>

      <div className="tooltip-row">
        <span className="tooltip-label">
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--forecast)' }} />
          Selected Forecast:
        </span>
        <span className="tooltip-value" style={{ color: 'var(--forecast)' }}>
          {data.forecastMw !== null ? `${formatMwPlain(data.forecastMw)} MW` : '—'}
        </span>
      </div>

      {data.errorMw !== null && (
        <div className="tooltip-row">
          <span className="tooltip-label">Signed Error (F - A):</span>
          <span
            className="tooltip-value"
            style={{ color: data.errorMw > 0 ? 'var(--forecast)' : '#FB923C' }}
          >
            {formatSignedMw(data.errorMw)}
          </span>
        </div>
      )}

      {data.localPublishTime && (
        <div className="tooltip-meta">
          Vintage: Published {data.localPublishTime} (Cut-off: 00:00 GMT)
        </div>
      )}
    </div>
  );
};

export const ForecastChart: React.FC<ForecastChartProps> = ({
  series,
  isSingleDay,
  selectedDate,
}) => {
  return (
    <div className="panel-card" data-testid="forecast-chart-card">
      <div className="panel-header">
        <div className="panel-title-group">
          <h2 className="panel-title">
            {isSingleDay ? `Generation Profile · ${selectedDate}` : 'Generation Profile · January 2026'}
          </h2>
          <span className="panel-description">
            Day-ahead selected forecast vs recorded FUELHH generation (Europe/London)
          </span>
        </div>

        <div className="series-legend">
          <div className="legend-item">
            <span className="legend-symbol forecast" aria-hidden="true" />
            <span>Forecast (MW)</span>
          </div>
          <div className="legend-item">
            <span className="legend-symbol actual" aria-hidden="true" />
            <span>Actual (MW)</span>
          </div>
        </div>
      </div>

      <div className="chart-container" style={{ width: '100%', height: 380 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="startTime"
              tickFormatter={(val) => isSingleDay ? formatHourMinute(val) : formatDateTime(val).split(',')[0]}
              tick={{ fontSize: 11, fill: 'var(--muted)' }}
              stroke="var(--border)"
              minTickGap={isSingleDay ? 15 : 45}
            />
            <YAxis
              tick={{ fontSize: 11, fill: 'var(--muted)' }}
              stroke="var(--border)"
              tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
              label={{
                value: 'Generation (MW)',
                angle: -90,
                position: 'insideLeft',
                offset: -5,
                style: { fill: 'var(--muted)', fontSize: 11, textAnchor: 'middle' },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="actualMw"
              name="Actual (MW)"
              stroke="var(--actual)"
              strokeWidth={2.4}
              dot={isSingleDay ? { r: 3, fill: 'var(--actual)' } : false}
              activeDot={{ r: 5, fill: 'var(--actual)' }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="forecastMw"
              name="Forecast (MW)"
              stroke="var(--forecast)"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={isSingleDay ? { r: 3, fill: 'var(--forecast)' } : false}
              activeDot={{ r: 5, fill: 'var(--forecast)' }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
