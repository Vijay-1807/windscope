import React, { useState, useEffect, useMemo } from 'react';
import { HelpCircle, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { Header } from '../components/Header';
import { KpiCards } from '../components/KpiCards';
import { ForecastChart } from '../components/ForecastChart';
import { DailyErrorChart } from '../components/DailyErrorChart';
import { IntervalTable } from '../components/IntervalTable';
import { MethodologyModal } from '../components/MethodologyModal';
import { StatusBanner } from '../components/StatusBanner';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/ErrorState';
import { fetchAnalysis } from '../lib/api';
import type { AnalysisResponse, IntervalRecord, MetricSummary } from '../types/api';
import { formatDateLabel } from '../lib/formatters';

export const App: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // View mode: 'month' | 'day'
  const [viewMode, setViewMode] = useState<'month' | 'day'>('month');
  const [selectedDate, setSelectedDate] = useState<string>('2026-01-15');
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchAnalysis('2026-01', true);
      setAnalysis(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to refresh forecast data');
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function initLoad() {
      try {
        const data = await fetchAnalysis('2026-01', false);
        if (!ignore) {
          setAnalysis(data);
          setError(null);
        }
      } catch (err: any) {
        if (!ignore) {
          setError(err.message || 'Failed to fetch analysis data');
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }
    initLoad();
    return () => {
      ignore = true;
    };
  }, []);

  // Available days in January 2026
  const availableDays = useMemo(() => {
    if (!analysis?.daily) return [];
    return analysis.daily.map((d) => d.date);
  }, [analysis]);

  // Current day index for prev/next
  const currentDayIndex = availableDays.indexOf(selectedDate);

  const handlePrevDay = () => {
    if (currentDayIndex > 0) {
      setSelectedDate(availableDays[currentDayIndex - 1]);
    }
  };

  const handleNextDay = () => {
    if (currentDayIndex < availableDays.length - 1) {
      setSelectedDate(availableDays[currentDayIndex + 1]);
    }
  };

  // Filtered series and metrics based on viewMode
  const displayedSeries: IntervalRecord[] = useMemo(() => {
    if (!analysis) return [];
    if (viewMode === 'month') return analysis.series;

    return analysis.series.filter((item) => {
      return item.startTime.startsWith(selectedDate) || item.localStartTime.startsWith(selectedDate);
    });
  }, [analysis, viewMode, selectedDate]);

  const displayedMetrics: MetricSummary | null = useMemo(() => {
    if (!analysis) return null;
    if (viewMode === 'month') return analysis.metrics;

    const daySummary = analysis.daily.find((d) => d.date === selectedDate);
    if (!daySummary) return null;

    return {
      mae: daySummary.mae,
      rmse: daySummary.rmse,
      bias: daySummary.bias,
      meanActual: daySummary.meanActual,
      normalizedMae:
        daySummary.mae !== null && daySummary.meanActual && daySummary.meanActual > 0
          ? Number(((daySummary.mae / daySummary.meanActual) * 100).toFixed(1))
          : null,
    };
  }, [analysis, viewMode, selectedDate]);

  const displayedMatchedCount = useMemo(() => {
    if (!analysis) return 0;
    if (viewMode === 'month') return analysis.matchedIntervals;
    const daySummary = analysis.daily.find((d) => d.date === selectedDate);
    return daySummary ? daySummary.matchedIntervals : 0;
  }, [analysis, viewMode, selectedDate]);

  const displayedExpectedCount = useMemo(() => {
    if (!analysis) return 1488;
    return viewMode === 'month' ? analysis.expectedIntervals : 48;
  }, [analysis, viewMode]);

  const displayedCoverage = useMemo(() => {
    if (!analysis) return 0;
    if (viewMode === 'month') return analysis.coveragePercent;
    const daySummary = analysis.daily.find((d) => d.date === selectedDate);
    return daySummary ? daySummary.coveragePercent : 0;
  }, [analysis, viewMode, selectedDate]);

  // Overall status
  const currentStatus = useMemo(() => {
    if (error) return 'error';
    if (!analysis) return 'loading';
    if (analysis.coveragePercent < 100) return 'partial';
    return 'loaded';
  }, [analysis, error]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !analysis) {
    return (
      <ErrorState
        error={error || 'No forecast data available'}
        onRetry={handleRefresh}
        isRetrying={isRefreshing}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Header
        status={currentStatus}
        lastUpdated={analysis.generatedAt ? analysis.generatedAt.replace('T', ' ').replace('Z', ' UTC') : null}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Page Headline & Context */}
      <section className="page-header">
        <div className="page-headline">
          <h1 className="page-title">Wind Forecast Accuracy</h1>
          <p className="page-subtitle">
            Great Britain · January 2026. Day-ahead gate evaluation vs FUELHH actuals.
          </p>
        </div>

        <div className="page-header-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setIsMethodologyOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={isMethodologyOpen}
          >
            <HelpCircle size={15} />
            <span>How this is calculated</span>
          </button>
        </div>
      </section>

      {/* Data Coverage Notice */}
      <StatusBanner
        warnings={analysis.warnings}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
      />

      {/* 4 KPI Cards */}
      <KpiCards
        metrics={displayedMetrics}
        matchedIntervals={displayedMatchedCount}
        expectedIntervals={displayedExpectedCount}
        coveragePercent={displayedCoverage}
      />

      {/* Timeframe Filters */}
      <section className="filter-bar" aria-label="Analysis timeframe filters">
        <div className="view-toggle-group" role="tablist">
          <button
            role="tab"
            aria-selected={viewMode === 'month'}
            className={`toggle-option ${viewMode === 'month' ? 'active' : ''}`}
            onClick={() => setViewMode('month')}
          >
            Whole Month (January 2026)
          </button>
          <button
            role="tab"
            aria-selected={viewMode === 'day'}
            className={`toggle-option ${viewMode === 'day' ? 'active' : ''}`}
            onClick={() => setViewMode('day')}
          >
            Single Delivery Day
          </button>
        </div>

        {viewMode === 'day' && (
          <div className="day-picker-group">
            <button
              className="btn btn-secondary"
              onClick={handlePrevDay}
              disabled={currentDayIndex <= 0}
              aria-label="Previous day"
              style={{ padding: '6px 10px', minHeight: 'auto' }}
            >
              <ChevronLeft size={15} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={15} color="var(--muted)" />
              <select
                className="day-select"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                aria-label="Select delivery date"
              >
                {availableDays.map((day) => (
                  <option key={day} value={day}>
                    {formatDateLabel(day)}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="btn btn-secondary"
              onClick={handleNextDay}
              disabled={currentDayIndex >= availableDays.length - 1}
              aria-label="Next day"
              style={{ padding: '6px 10px', minHeight: 'auto' }}
            >
              <ChevronRight size={15} />
            </button>
          </div>
        )}
      </section>

      {/* Primary Forecast vs Actual Chart */}
      <ForecastChart
        series={displayedSeries}
        isSingleDay={viewMode === 'day'}
        selectedDate={formatDateLabel(selectedDate)}
      />

      {/* Daily Error Summary Bar Chart */}
      <DailyErrorChart
        daily={analysis.daily}
        selectedDate={viewMode === 'day' ? selectedDate : null}
        onSelectDate={(date) => {
          setSelectedDate(date);
          setViewMode('day');
        }}
      />

      {/* Half-hourly Interval Detail Table */}
      <IntervalTable
        intervals={displayedSeries}
        title={viewMode === 'day' ? `Interval Details · ${formatDateLabel(selectedDate)}` : 'Target Interval Details'}
        subtitle={
          viewMode === 'day'
            ? `48 half-hour settlement periods for ${selectedDate} (Europe/London)`
            : '1,488 expected half-hour settlement periods across January 2026'
        }
      />

      {/* Methodology Modal */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
        decisionCutoffDescription={analysis.decisionCutoffDescription}
      />
    </div>
  );
};
