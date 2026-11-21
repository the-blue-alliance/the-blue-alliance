import lighthouse from 'lighthouse';
import desktopConfig from 'lighthouse/core/config/desktop-config.js';

export type FormFactor = 'mobile' | 'desktop';

export const METRIC_LABELS = {
  performanceScore: 'Perf score (0-100)',
  firstContentfulPaint: 'FCP (ms)',
  largestContentfulPaint: 'LCP (ms)',
  totalBlockingTime: 'TBT (ms)',
  cumulativeLayoutShift: 'CLS',
  speedIndex: 'Speed Index (ms)',
  interactive: 'TTI (ms)',
  serverResponseTime: 'TTFB (ms)',
} as const;

export type MetricKey = keyof typeof METRIC_LABELS;
export type MetricRun = Record<MetricKey, number>;

const AUDIT_IDS: Record<Exclude<MetricKey, 'performanceScore'>, string> = {
  firstContentfulPaint: 'first-contentful-paint',
  largestContentfulPaint: 'largest-contentful-paint',
  totalBlockingTime: 'total-blocking-time',
  cumulativeLayoutShift: 'cumulative-layout-shift',
  speedIndex: 'speed-index',
  interactive: 'interactive',
  serverResponseTime: 'server-response-time',
};

export interface LighthouseRun {
  metrics: MetricRun;
  htmlReport: string;
}

export async function runLighthouse(
  url: string,
  port: number,
  formFactor: FormFactor,
): Promise<LighthouseRun> {
  const result = await lighthouse(
    url,
    {
      port,
      output: 'html',
      logLevel: 'error',
      onlyCategories: ['performance'],
    },
    formFactor === 'desktop' ? desktopConfig : undefined,
  );

  if (!result) throw new Error(`Lighthouse returned no result for ${url}`);
  const { lhr } = result;

  if (lhr.runtimeError) {
    throw new Error(`Lighthouse runtime error: ${lhr.runtimeError.message}`);
  }

  const metrics = {
    performanceScore: (lhr.categories.performance?.score ?? 0) * 100,
  } as MetricRun;

  for (const [key, auditId] of Object.entries(AUDIT_IDS)) {
    metrics[key as MetricKey] = lhr.audits[auditId]?.numericValue ?? NaN;
  }

  return {
    metrics,
    htmlReport: Array.isArray(result.report) ? result.report[0] : result.report,
  };
}
