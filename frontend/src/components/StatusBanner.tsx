import React from 'react';
import { Info, ArrowRight } from 'lucide-react';

interface StatusBannerProps {
  warnings: string[];
  onOpenMethodology: () => void;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ warnings, onOpenMethodology }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <aside className="alert-banner warning" role="region" aria-label="Data coverage notices">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', flex: 1 }}>
        <span className="notice-pill">
          <Info size={12} />
          COVERAGE
        </span>
        <span style={{ fontSize: '0.8125rem', color: 'var(--ink)' }}>
          {warnings[0]}
        </span>
      </div>

      <button
        onClick={onOpenMethodology}
        className="btn btn-secondary"
        style={{
          padding: '4px 10px',
          minHeight: '28px',
          fontSize: '0.75rem',
          fontWeight: 600,
          gap: '4px',
          flexShrink: 0,
        }}
        aria-label="View calculation methodology"
      >
        <span>Methodology</span>
        <ArrowRight size={12} />
      </button>
    </aside>
  );
};
