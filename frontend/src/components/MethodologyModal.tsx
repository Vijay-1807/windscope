import React, { useEffect, useRef } from 'react';
import { X, BookOpen, Clock, ShieldCheck, Calculator, AlertTriangle } from 'lucide-react';

interface MethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
  decisionCutoffDescription?: string;
}

export const MethodologyModal: React.FC<MethodologyModalProps> = ({
  isOpen,
  onClose,
  decisionCutoffDescription,
}) => {
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeBtnRef.current?.focus();
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="methodology-modal-title"
    >
      <div className="modal-content">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <BookOpen size={18} color="var(--primary)" />
            <h2 id="methodology-modal-title" className="modal-title">
              Methodology & Calculation Rules
            </h2>
          </div>
          <button
            ref={closeBtnRef}
            className="btn btn-subtle"
            onClick={onClose}
            aria-label="Close methodology modal"
            style={{ padding: '6px', minHeight: 'auto', borderRadius: '50%' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* Section 1: Decision Cut-off Policy */}
          <div className="modal-section">
            <h3 className="modal-section-title">
              <Clock size={15} color="var(--primary)" />
              1. Day-Ahead Decision Cut-off Rule
            </h3>
            <p>
              In UK wholesale power markets, day-ahead energy procurement commitments close prior to the start of the delivery day. To evaluate the exact forecast available at gate closure without look-ahead bias:
            </p>
            <blockquote
              style={{
                background: 'var(--surface-muted)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                borderLeft: '3px solid var(--primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem',
                margin: '4px 0',
                color: 'var(--ink)',
              }}
            >
              publishTime &lt; start_of_delivery_date_in_Europe_London
            </blockquote>
            <p style={{ fontSize: '0.8125rem' }}>
              {decisionCutoffDescription ||
                'Only forecasts published strictly before midnight local time on date D are eligible. From all eligible vintages, the latest published forecast is selected.'}
            </p>
          </div>

          {/* Section 2: Data Sources */}
          <div className="modal-section">
            <h3 className="modal-section-title">
              <ShieldCheck size={15} color="var(--primary)" />
              2. Data Contracts & Upstream Endpoints
            </h3>
            <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8125rem' }}>
              <li>
                <strong>Actuals (FUELHH):</strong> Generation by Fuel Type stream, filtered to <code>fuelType=WIND</code>. Half-hourly cadence.
              </li>
              <li>
                <strong>Forecast Vintages (WINDFOR):</strong> National wind generation forecasts stream. Historical publication vintages joined on target <code>startTime</code>.
              </li>
            </ul>
          </div>

          {/* Section 3: Metrics */}
          <div className="modal-section">
            <h3 className="modal-section-title">
              <Calculator size={15} color="var(--primary)" />
              3. Forecast Accuracy Formulations
            </h3>
            <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8125rem' }}>
              <li>
                <strong>MAE (Mean Absolute Error):</strong> <code>mean(|Forecast - Actual|)</code>. Unsigned magnitude of deviation in MW.
              </li>
              <li>
                <strong>RMSE (Root Mean Square Error):</strong> <code>sqrt(mean((Forecast - Actual)²))</code>. Standard deviation of residuals; penalizes severe misses.
              </li>
              <li>
                <strong>Mean Bias:</strong> <code>mean(Forecast - Actual)</code>. Signed directional bias (positive = over-forecast, negative = under-forecast).
              </li>
              <li>
                <strong>Normalized MAE:</strong> <code>(MAE / mean(Actual)) × 100%</code>. Relative error scaled by average generation. Ordinary MAPE is avoided due to division-by-zero instability during low-wind intervals.
              </li>
            </ul>
          </div>

          {/* Section 4: Resolution & Coverage */}
          <div className="modal-section">
            <h3 className="modal-section-title">
              <AlertTriangle size={15} color="var(--warning)" />
              4. Data Resolution & Missing Values
            </h3>
            <p style={{ fontSize: '0.8125rem' }}>
              January 2026 comprises 1,488 half-hour intervals (31 days × 48). While FUELHH provides actuals for all 1,488 intervals, WINDFOR forecasts are published at hourly timestamps (:00), yielding 744 matched intervals (50.0% coverage).
            </p>
            <p style={{ fontSize: '0.8125rem' }}>
              Unmatched half-hours (:30) display recorded generation with error metrics marked unavailable. <strong>Zero-filling is strictly prohibited</strong> to avoid distortion of market metrics.
            </p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
