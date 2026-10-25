import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  error: string;
  onRetry: () => void;
  isRetrying?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry, isRetrying }) => {
  return (
    <div className="app-container" style={{ minHeight: '80vh', justifyContent: 'center' }}>
      <div
        className="panel-card"
        style={{
          maxWidth: 580,
          margin: '0 auto',
          textAlign: 'center',
          alignItems: 'center',
          padding: '40px 24px',
        }}
        role="alert"
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'var(--danger-subtle)',
            color: 'var(--danger)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 16,
          }}
        >
          <AlertCircle size={28} />
        </div>

        <h2 style={{ fontSize: '1.25rem', marginBottom: 8, color: 'var(--ink)' }}>
          Failed to Load Wind Forecast Analysis
        </h2>

        <p style={{ color: 'var(--muted)', fontSize: '0.9375rem', marginBottom: 24, lineHeight: 1.5 }}>
          {error || 'Unable to communicate with the analysis backend service or upstream Elexon data source.'}
        </p>

        <button className="btn btn-primary" onClick={onRetry} disabled={isRetrying}>
          <RefreshCw size={16} className={isRetrying ? 'spin-animation' : ''} />
          <span>{isRetrying ? 'Retrying...' : 'Retry Request'}</span>
        </button>
      </div>
    </div>
  );
};
