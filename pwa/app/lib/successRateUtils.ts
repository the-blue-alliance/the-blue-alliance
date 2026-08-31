export type MatchLevel = 'qual' | 'playoff';

export function otherMatchLevel(level: MatchLevel): MatchLevel {
  return level === 'qual' ? 'playoff' : 'qual';
}

/**
 * Success rates are stored as a count out of a number of opportunities, so the
 * percentage is derived here rather than on the wire. A scope with no
 * opportunities renders as a dash instead of 0%.
 */
export function formatSuccessRate({
  count,
  opportunities,
}: {
  count: number;
  opportunities: number;
}): string {
  if (opportunities === 0) {
    return '—';
  }
  return `${((100 * count) / opportunities).toFixed(2)}%`;
}
