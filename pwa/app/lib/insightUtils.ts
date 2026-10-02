import { type InsightV2Timeseries } from '~/api/tba/read';

/** Number of rows shown before a "top N" table's expand toggle is used. */
export const PRE_EXPANDED_ROWS = 10;

type TimeseriesData = InsightV2Timeseries['data'];
type TimeseriesPoint = TimeseriesData['series'][number]['points'][number];

export interface RecordContext {
  matchKey?: string;
  alliance?: string[];
  postResultTime?: number;
  isCurrent?: boolean;
  /** post_result_time of the record that overtook this one, if any. */
  heldUntilPostResultTime?: number;
}

export interface ChartRow {
  x: string | number;
  [seriesKey: string]: string | number | RecordContext | undefined;
}

/**
 * Whether the timeseries renders on a numeric time x-axis (points sorted and
 * spaced by an actual instant) rather than a categorical one. True for
 * `date`-typed series and for `match_record` series, whose real x is
 * `context.post_result_time`.
 */
export function timeseriesHasTemporalXAxis(data: TimeseriesData): boolean {
  return data.x_type === 'date' || data.point_context_type === 'match_record';
}

export function contextKey(seriesLabel: string): string {
  return `${seriesLabel}__ctx`;
}

/**
 * `match_record` points all share a coarse `x` (e.g. the season year), since
 * `x` only labels which timeseries the point belongs to. The actual moment
 * the record was set is `context.post_result_time`, which is what should
 * drive the chart's x-axis so every record shows up as its own point.
 */
function effectiveX(
  point: TimeseriesPoint,
  usePostResultTime: boolean,
): string | number {
  if (usePostResultTime && point.context?.post_result_time !== undefined) {
    return point.context.post_result_time;
  }
  return point.x;
}

/**
 * Merges the timeseries' per-series points into a single array of rows keyed
 * by (effective) `x`, one column per series label, for recharts' wide-format
 * `LineChart`. When points carry match-record context, each row also carries
 * a parallel `<label>__ctx` entry so the tooltip can show who set the record,
 * when, and how long they held it.
 */
export function mergeSeries(data: TimeseriesData): ChartRow[] {
  const usePostResultTime = data.point_context_type === 'match_record';
  const temporal = timeseriesHasTemporalXAxis(data);

  const orderedX: Array<string | number> = [];
  const seenX = new Set<string>();
  const valuesByKey = new Map<string, number>();
  const contextByKey = new Map<string, RecordContext>();

  for (const series of data.series) {
    series.points.forEach((point, i) => {
      const x = effectiveX(point, usePostResultTime);
      const xKey = String(x);
      if (!seenX.has(xKey)) {
        seenX.add(xKey);
        orderedX.push(x);
      }
      const rowKey = `${series.label} ${xKey}`;
      valuesByKey.set(rowKey, point.y);

      if (point.context) {
        const nextPoint = series.points[i + 1];
        contextByKey.set(rowKey, {
          matchKey: point.context.match_key,
          alliance: point.context.alliance,
          postResultTime: point.context.post_result_time,
          isCurrent: point.context.is_current,
          heldUntilPostResultTime: nextPoint?.context?.post_result_time,
        });
      }
    });
  }

  if (temporal) {
    orderedX.sort((a, b) => Number(a) - Number(b));
  }

  return orderedX.map((x) => {
    const row: ChartRow = { x };
    for (const series of data.series) {
      const rowKey = `${series.label} ${String(x)}`;
      const y = valuesByKey.get(rowKey);
      if (y !== undefined) {
        row[series.label] = y;
      }
      const context = contextByKey.get(rowKey);
      if (context) {
        row[contextKey(series.label)] = context;
      }
    }
    return row;
  });
}

type RankPosition = 1 | 2 | 3;

/** Row background/border accents for the top 3 ranks of a leaderboard-style table. */
const RANK_ROW_COLORS: Record<RankPosition, string> = {
  1: 'bg-yellow-500/10 border-l-4 border-l-yellow-500',
  2: 'bg-gray-400/10 border-l-4 border-l-gray-400',
  3: 'bg-orange-600/10 border-l-4 border-l-orange-600',
};

/** Text accents for the top 3 ranks of a leaderboard-style table. */
const RANK_TEXT_COLORS: Record<RankPosition, string> = {
  1: 'text-yellow-600 dark:text-yellow-400',
  2: 'text-gray-600 dark:text-gray-400',
  3: 'text-orange-600 dark:text-orange-500',
};

export function rankRowClassName(rank: number): string | undefined {
  return rank <= 3 ? RANK_ROW_COLORS[rank as RankPosition] : undefined;
}

export function rankTextClassName(rank: number): string | undefined {
  return rank <= 3 ? RANK_TEXT_COLORS[rank as RankPosition] : undefined;
}
