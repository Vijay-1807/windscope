import React, { useState, useMemo } from 'react';
import { Download, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';
import type { IntervalRecord } from '../types/api';
import { formatMwPlain, formatSignedMw, formatDateTime } from '../lib/formatters';

interface IntervalTableProps {
  intervals: IntervalRecord[];
  title?: string;
  subtitle?: string;
}

type SortField = 'startTime' | 'actualMw' | 'forecastMw' | 'errorMw' | 'absoluteErrorMw';
type SortOrder = 'asc' | 'desc';

export const IntervalTable: React.FC<IntervalTableProps> = ({
  intervals,
  title = 'Target Interval Detail',
  subtitle = 'Individual half-hourly delivery intervals and selected forecast vintages',
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(24);
  const [sortField, setSortField] = useState<SortField>('startTime');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Sorting
  const sortedIntervals = useMemo(() => {
    return [...intervals].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortOrder === 'asc' ? valA - valB : valB - valA;
      }

      return 0;
    });
  }, [intervals, sortField, sortOrder]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(sortedIntervals.length / pageSize));
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedIntervals.slice(start, start + pageSize);
  }, [sortedIntervals, currentPage, pageSize]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleExportCsv = () => {
    const headers = [
      'Target Delivery Time (UTC)',
      'Target Delivery Time (London)',
      'Actual Generation (MW)',
      'Selected Forecast (MW)',
      'Forecast Published At (London)',
      'Signed Error (MW)',
      'Absolute Error (MW)',
    ];

    const rows = sortedIntervals.map((row) => [
      row.startTime,
      row.localStartTime,
      row.actualMw !== null ? row.actualMw : '',
      row.forecastMw !== null ? row.forecastMw : '',
      row.localPublishTime || '',
      row.errorMw !== null ? row.errorMw : '',
      row.absoluteErrorMw !== null ? row.absoluteErrorMw : '',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.map((val) => `"${val}"`).join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `windscope_intervals_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="panel-card" data-testid="interval-table-card">
      <div className="panel-header">
        <div className="panel-title-group">
          <h2 className="panel-title">{title}</h2>
          <span className="panel-description">{subtitle}</span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={handleExportCsv}
          title="Export displayed records to CSV"
          aria-label="Export CSV"
        >
          <Download size={15} />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="table-wrapper" tabIndex={0} aria-label="Interval records table">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" onClick={() => handleSort('startTime')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Delivery Time (London)</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th scope="col" onClick={() => handleSort('forecastMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Forecast (MW)</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th scope="col" onClick={() => handleSort('actualMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Actual (MW)</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th scope="col" onClick={() => handleSort('errorMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Signed Error (MW)</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th scope="col" onClick={() => handleSort('absoluteErrorMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Abs Error (MW)</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th scope="col">Forecast Published At</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--muted)' }}>
                  No interval records found.
                </td>
              </tr>
            ) : (
              paginatedData.map((row) => (
                <tr key={row.startTime}>
                  <td>
                    <strong>{row.localStartTime || formatDateTime(row.startTime)}</strong>
                  </td>
                  <td>
                    {row.forecastMw !== null ? (
                      formatMwPlain(row.forecastMw)
                    ) : (
                      <span className="cell-na" title="No hourly forecast published for this half-hour">
                        —
                      </span>
                    )}
                  </td>
                  <td>
                    {row.actualMw !== null ? (
                      formatMwPlain(row.actualMw)
                    ) : (
                      <span className="cell-na">Not available</span>
                    )}
                  </td>
                  <td>
                    {row.errorMw !== null ? (
                      <span className={row.errorMw > 0 ? 'cell-positive' : row.errorMw < 0 ? 'cell-negative' : ''}>
                        {formatSignedMw(row.errorMw)}
                      </span>
                    ) : (
                      <span className="cell-na">—</span>
                    )}
                  </td>
                  <td>
                    {row.absoluteErrorMw !== null ? (
                      formatMwPlain(row.absoluteErrorMw)
                    ) : (
                      <span className="cell-na">—</span>
                    )}
                  </td>
                  <td style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>
                    {row.localPublishTime ? (
                      <span>{row.localPublishTime}</span>
                    ) : (
                      <span className="cell-na">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination-bar">
        <div>
          Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, sortedIntervals.length)} of{' '}
          {sortedIntervals.length} intervals
        </div>

        <div className="pagination-controls">
          <label htmlFor="page-size-select" style={{ fontSize: '0.8125rem' }}>
            Rows per page:
          </label>
          <select
            id="page-size-select"
            className="day-select"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            style={{ padding: '4px 8px', fontSize: '0.8125rem' }}
          >
            <option value={24}>24</option>
            <option value={48}>48</option>
            <option value={96}>96</option>
          </select>

          <button
            className="btn btn-secondary"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            aria-label="Previous page"
            style={{ padding: '6px 10px', minHeight: 'auto' }}
          >
            <ChevronLeft size={16} />
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            aria-label="Next page"
            style={{ padding: '6px 10px', minHeight: 'auto' }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
