import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="app-container" aria-busy="true" aria-label="Loading forecast accuracy dashboard">
      {/* Top Bar Skeleton */}
      <div className="skeleton" style={{ height: 60, width: '100%', borderRadius: 'var(--radius-lg)' }} />

      {/* Header Skeleton */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, margin: '8px 0' }}>
        <div className="skeleton" style={{ height: 36, width: '40%' }} />
        <div className="skeleton" style={{ height: 20, width: '60%' }} />
      </div>

      {/* KPI Cards Skeleton */}
      <div className="kpi-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="skeleton" style={{ height: 130, borderRadius: 'var(--radius-lg)' }} />
        ))}
      </div>

      {/* Filter Bar Skeleton */}
      <div className="skeleton" style={{ height: 52, borderRadius: 'var(--radius-lg)' }} />

      {/* Main Chart Skeleton */}
      <div className="skeleton" style={{ height: 420, borderRadius: 'var(--radius-lg)' }} />

      {/* Daily Chart Skeleton */}
      <div className="skeleton" style={{ height: 300, borderRadius: 'var(--radius-lg)' }} />

      {/* Table Skeleton */}
      <div className="skeleton" style={{ height: 350, borderRadius: 'var(--radius-lg)' }} />
    </div>
  );
};
