export function formatMw(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  }).format(val) + ' MW';
}

export function formatMwPlain(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  }).format(val);
}

export function formatSignedMw(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  const sign = val > 0 ? '+' : '';
  return sign + new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  }).format(val) + ' MW';
}

export function formatPercent(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return val.toFixed(1) + '%';
}

export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-GB', {
      timeZone: 'Europe/London',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export function formatHourMinute(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-GB', {
      timeZone: 'Europe/London',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

export function formatDateLabel(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const [year, month, day] = dateStr.split('-').map(Number);
    const d = new Date(Date.UTC(year, month - 1, day));
    return d.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC',
    });
  } catch {
    return dateStr;
  }
}
