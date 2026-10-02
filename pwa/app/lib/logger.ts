import pino from 'pino';

// Map Pino log levels to Google Cloud Logging severity levels
const PINO_TO_GCP_SEVERITY: Record<string, string> = {
  10: 'DEBUG', // trace
  20: 'DEBUG', // debug
  30: 'INFO', // info
  40: 'WARNING', // warn
  50: 'ERROR', // error
  60: 'CRITICAL', // fatal
};

/**
 * pino `formatters.log`: moves custom fields (from both the mixin and the log
 * call) under Google Cloud Logging's labels key. The mixin in `createLogger`
 * always contributes `logger`, so in practice the object is never empty; an
 * empty object yields no labels key rather than an empty one.
 */
export function formatGcpLogLabels(
  object: Record<string, unknown>,
): Record<string, unknown> {
  if (Object.keys(object).length === 0) {
    return {};
  }

  return {
    'logging.googleapis.com/labels': object,
  };
}

export function createLogger(name: string) {
  const isDev = process.env.NODE_ENV !== 'production';

  if (isDev) {
    // In development, use pino-pretty for human-readable output
    return pino({
      name,
      transport: { target: 'pino-pretty' },
    });
  }

  // In production (App Engine), output structured JSON for Cloud Logging
  // See: https://cloud.google.com/run/docs/logging#writing-structured-logs
  return pino({
    name,
    // Hot-path diagnostics log at debug; set LOG_LEVEL=debug to see them.
    level: process.env.LOG_LEVEL ?? 'info',
    // Use 'message' instead of 'msg' for Google Cloud Logging compatibility
    messageKey: 'message',
    // Omit default base fields (pid, hostname) - not needed for Cloud Logging
    base: undefined,
    // Format logs for Google Cloud Logging
    formatters: {
      level(label, number) {
        return { severity: PINO_TO_GCP_SEVERITY[number] || 'INFO' };
      },
      log: formatGcpLogLabels,
    },
    // Add logger name to every log entry (will be picked up by log formatter)
    mixin() {
      return {
        logger: name,
      };
    },
  });
}
