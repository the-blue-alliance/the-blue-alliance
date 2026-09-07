export interface MetricSummary {
  min: number;
  median: number;
  p90: number;
  max: number;
  mean: number;
  stddev: number;
}

export function percentile(values: number[], p: number): number {
  if (values.length === 0) return NaN;
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 1) return sorted[0];
  const rank = (p / 100) * (sorted.length - 1);
  const low = Math.floor(rank);
  const high = Math.ceil(rank);
  if (low === high) return sorted[low];
  return sorted[low] + (sorted[high] - sorted[low]) * (rank - low);
}

export function mean(values: number[]): number {
  if (values.length === 0) return NaN;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

export function stddev(values: number[]): number {
  if (values.length < 2) return 0;
  const avg = mean(values);
  const variance =
    values.reduce((sum, v) => sum + (v - avg) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

export function summarize(values: number[]): MetricSummary {
  return {
    min: Math.min(...values),
    median: percentile(values, 50),
    p90: percentile(values, 90),
    max: Math.max(...values),
    mean: mean(values),
    stddev: stddev(values),
  };
}

export function summarizeRuns<K extends string>(
  runs: Record<K, number>[],
): Record<K, MetricSummary> {
  const keys = Object.keys(runs[0]) as K[];
  const out = {} as Record<K, MetricSummary>;
  for (const key of keys) {
    out[key] = summarize(runs.map((run) => run[key]));
  }
  return out;
}
