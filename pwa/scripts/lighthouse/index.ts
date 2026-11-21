import { writeFileSync } from 'node:fs';
import process from 'node:process';
import { parseArgs } from 'node:util';

import { launchBrowser } from './browser';
import {
  type FormFactor,
  METRIC_LABELS,
  type MetricKey,
  type MetricRun,
  runLighthouse,
} from './run';
import { serve } from './serve';
import { summarizeRuns } from './stats';

function fail(message: string): never {
  console.error(`✗ ${message}`);
  process.exit(1);
}

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    repeat: { type: 'string', default: '5' },
    warmup: { type: 'string', default: '0' },
    'form-factor': { type: 'string', default: 'mobile' },
    url: { type: 'string', default: 'http://localhost:3000' },
    json: { type: 'string' },
    report: { type: 'string' },
    'no-server': { type: 'boolean', default: false },
  },
});

const route = positionals[0];
if (!route || !route.startsWith('/')) {
  fail(
    'Usage: pnpm run lighthouse <route> [--repeat N] [--warmup N] [--form-factor mobile|desktop] [--url base] [--json path] [--report path.html] [--no-server]',
  );
}

const repeat = Number(values.repeat);
if (!Number.isInteger(repeat) || repeat < 1) {
  fail(`--repeat must be a positive integer, got "${values.repeat}"`);
}

const warmup = Number(values.warmup);
if (!Number.isInteger(warmup) || warmup < 0) {
  fail(`--warmup must be a non-negative integer, got "${values.warmup}"`);
}

const formFactor = values['form-factor'] as FormFactor;
if (formFactor !== 'mobile' && formFactor !== 'desktop') {
  fail(
    `--form-factor must be "mobile" or "desktop", got "${values['form-factor']}"`,
  );
}

const baseUrl = values.url.replace(/\/$/, '');
const targetUrl = `${baseUrl}${route}`;
const isLocalhost = /^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(
  baseUrl,
);
const autoServe = !values['no-server'] && isLocalhost;

function pad(value: string, width: number): string {
  return value.padStart(width);
}

function formatNumber(key: MetricKey, value: number): string {
  if (Number.isNaN(value)) return 'n/a';
  return key === 'cumulativeLayoutShift'
    ? value.toFixed(3)
    : Math.round(value).toString();
}

async function main(): Promise<void> {
  const server = await serve(baseUrl, { autoServe });
  const browser = await launchBrowser();

  const runs: MetricRun[] = [];
  let lastHtmlReport = '';
  try {
    for (let i = 1; i <= warmup; i += 1) {
      process.stdout.write(`  warmup ${i}/${warmup}... `);
      await runLighthouse(targetUrl, browser.port, formFactor);
      console.log('discarded');
    }
    for (let i = 1; i <= repeat; i += 1) {
      process.stdout.write(`  run ${i}/${repeat}... `);
      const { metrics, htmlReport } = await runLighthouse(
        targetUrl,
        browser.port,
        formFactor,
      );
      runs.push(metrics);
      lastHtmlReport = htmlReport;
      console.log(
        `LCP ${formatNumber('largestContentfulPaint', metrics.largestContentfulPaint)}ms  ` +
          `score ${formatNumber('performanceScore', metrics.performanceScore)}`,
      );
    }
  } finally {
    await browser.close();
    await server.teardown();
  }

  const summary = summarizeRuns(runs);
  const keys = Object.keys(METRIC_LABELS) as MetricKey[];
  const labelWidth = Math.max(...keys.map((k) => METRIC_LABELS[k].length));
  const cols = ['median', 'p90', 'min', 'max', 'stddev'] as const;

  const warmupNote = warmup > 0 ? ` (+${warmup} discarded)` : '';
  console.log(
    `\nRoute ${route}  •  ${repeat} runs${warmupNote}  •  ${formFactor}  •  ${baseUrl}\n`,
  );
  console.log(
    `${pad('metric', labelWidth)}  ${cols.map((c) => pad(c, 9)).join('  ')}`,
  );
  for (const key of keys) {
    const s = summary[key];
    const row = [s.median, s.p90, s.min, s.max, s.stddev]
      .map((v) => pad(formatNumber(key, v), 9))
      .join('  ');
    console.log(`${pad(METRIC_LABELS[key], labelWidth)}  ${row}`);
  }

  if (values.json) {
    writeFileSync(
      values.json,
      JSON.stringify(
        {
          route,
          url: targetUrl,
          formFactor,
          repeat,
          warmup,
          timestamp: new Date().toISOString(),
          runs,
          summary,
        },
        null,
        2,
      ),
    );
    console.log(`\n↳ Wrote ${values.json}`);
  }

  if (values.report) {
    writeFileSync(values.report, lastHtmlReport);
    console.log(`↳ Wrote ${values.report} (HTML report, final run)`);
  }
}

main().catch((error) => {
  fail(error instanceof Error ? error.message : String(error));
});
