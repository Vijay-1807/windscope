import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import type { DailySummary } from '../types/api';
import { formatMwPlain } from '../lib/formatters';

interface DailyErrorChartProps {
  daily: DailySummary[];
  selectedDate: string | null;
  onSelectDate: (date: string) => void;
}

interface DailyTooltipProps {
  active?: boolean;
  payload?: any[];
}

const DailyTooltip: React.FC<DailyTooltipProps> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const item: DailySummary = payload[0]?.payload;
  if (!item) return null;

  return (
    <div className="custom-tooltip" role="tooltip">
      <div className="tooltip-title">{item.date}</div>
      <div className="tooltip-row">
        <span className="tooltip-label">Daily MAE:</span>
        <span className="tooltip-value" style={{ color: 'var(--primary)' }}>
          {item.mae !== null ? `${formatMwPlain(item.mae)} MW` : '—'}
        </span>
      </div>
      <div className="tooltip-row">
        <span className="tooltip-label">Daily RMSE:</span>
        <span className="tooltip-value">
          {item.rmse !== null ? `${formatMwPlain(item.rmse)} MW` : '—'}
        </span>
      </div>
      <div className="tooltip-row">
        <span className="tooltip-label">Daily Bias:</span>
        <span
          className="tooltip-value"
          style={{ color: item.bias && item.bias > 0 ? 'var(--forecast)' : '#FB923C' }}
        >
          {item.bias !== null ? `${item.bias > 0 ? '+' : ''}${formatMwPlain(item.bias)} MW` : '—'}
        </span>
      </div>
      <div className="tooltip-meta">
        {item.matchedIntervals} / {item.expectedIntervals} intervals ({item.coveragePercent}% coverage)
      </div>
    </div>
  );
};

export const DailyErrorChart: React.FC<DailyErrorChartProps> = ({
  daily,
  selectedDate,
  onSelectDate,
}) => {
  return (
    <div className="panel-card" data-testid="daily-error-chart-card">
      <div className="panel-header">
        <div className="panel-title-group">
          <h2 className="panel-title">Daily Mean Absolute Error (MAE)</h2>
          <span className="panel-description">
            Mean absolute error by delivery day (MW). Click bar to inspect day.
          </span>
        </div>
      </div>

      <div className="chart-container" style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={daily} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(val) => val.split('-')[2]}
              tick={{ fontSize: 11, fill: 'var(--muted)' }}
              stroke="var(--border)"
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11, fill: 'var(--muted)' }}
              stroke="var(--border)"
              tickFormatter={(val) => `${val}`}
              label={{
                value: 'MAE (MW)',
                angle: -90,
                position: 'insideLeft',
                offset: -5,
                style: { fill: 'var(--muted)', fontSize: 11, textAnchor: 'middle' },
              }}
            />
            <Tooltip content={<DailyTooltip />} />
            <Bar
              dataKey="mae"
              name="Daily MAE"
              radius={[4, 4, 0, 0]}
              onClick={(entry: any) => {
                if (entry && entry.date) onSelectDate(entry.date);
              }}
              cursor="pointer"
            >
              {daily.map((entry) => (
                <Cell
                  key={entry.date}
                  fill={entry.date === selectedDate ? 'var(--primary)' : 'var(--primary)'}
                  opacity={selectedDate && entry.date !== selectedDate ? 0.35 : 0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
