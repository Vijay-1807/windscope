import React, { useState, useEffect } from 'react';
import { Wind, RefreshCw, AlertCircle, CheckCircle2, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  status: 'loading' | 'loaded' | 'partial' | 'error';
  lastUpdated: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  lastUpdated,
  onRefresh,
  isRefreshing,
}) => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const saved = localStorage.getItem('windscope-theme') as 'dark' | 'light' | null;
    if (saved) {
      setTheme(saved);
      document.documentElement.setAttribute('data-theme', saved);
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('windscope-theme', next);
  };

  return (
    <header className="top-bar" role="banner">
      <div className="brand-section">
        <div className="brand-logo" aria-hidden="true">
          <Wind size={20} strokeWidth={2.2} />
        </div>
        <div className="brand-text">
          <span className="brand-title">WindScope</span>
          <span className="brand-badge">GB National Grid · Elexon BMRS</span>
        </div>
      </div>

      <div className="top-bar-actions">
        {status === 'loaded' && (
          <div className="status-pill loaded" aria-label="Status: Data loaded successfully">
            <CheckCircle2 size={13} className="status-dot-icon" />
            <span>Operational</span>
          </div>
        )}
        {status === 'partial' && (
          <div className="status-pill partial" aria-label="Status: Partial data available">
            <span className="status-dot" />
            <span>Partial Data (50% Coverage)</span>
          </div>
        )}
        {status === 'error' && (
          <div className="status-pill error" aria-label="Status: Data unavailable">
            <AlertCircle size={13} />
            <span>Service Offline</span>
          </div>
        )}

        {lastUpdated && (
          <span className="brand-badge" title="Data last synchronized">
            Synced {lastUpdated}
          </span>
        )}

        <button
          className="btn btn-secondary"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          title="Toggle light/dark theme"
          style={{ padding: '7px 10px' }}
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        <button
          className="btn btn-secondary"
          onClick={onRefresh}
          disabled={isRefreshing}
          aria-label={isRefreshing ? 'Refreshing forecast data...' : 'Refresh data'}
          title="Re-query upstream Elexon BMRS"
        >
          <RefreshCw
            size={14}
            className={isRefreshing ? 'spin-animation' : ''}
            style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }}
          />
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </header>
  );
};
