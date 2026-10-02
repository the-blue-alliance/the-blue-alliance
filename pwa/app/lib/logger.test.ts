import { describe, expect, test, vi } from 'vitest';

import { createLogger, formatGcpLogLabels } from '~/lib/logger';

describe('createLogger', () => {
  test('defaults to info in production, so debug hot-path logs are not emitted', () => {
    vi.stubEnv('NODE_ENV', 'production');
    vi.stubEnv('LOG_LEVEL', undefined);

    const logger = createLogger('test');

    expect(logger.level).toEqual('info');
    expect(logger.isLevelEnabled('debug')).toBe(false);
    expect(logger.isLevelEnabled('warn')).toBe(true);
  });

  test('honors LOG_LEVEL so hot-path diagnostics can be turned back on', () => {
    vi.stubEnv('NODE_ENV', 'production');
    vi.stubEnv('LOG_LEVEL', 'debug');

    const logger = createLogger('test');

    expect(logger.level).toEqual('debug');
    expect(logger.isLevelEnabled('debug')).toBe(true);
  });
});

describe('createLogger production output', () => {
  test('writes Google Cloud structured log lines', () => {
    vi.stubEnv('NODE_ENV', 'production');
    const write = vi
      .spyOn(process.stdout, 'write')
      .mockImplementation(() => true);

    createLogger('svc').warn({ requestId: 'abc' }, 'slow request');

    expect(JSON.parse(String(write.mock.calls[0][0]))).toMatchObject({
      severity: 'WARNING',
      message: 'slow request',
      'logging.googleapis.com/labels': { logger: 'svc', requestId: 'abc' },
    });
  });

  test('labels every line with the logger name even without extra fields', () => {
    vi.stubEnv('NODE_ENV', 'production');
    const write = vi
      .spyOn(process.stdout, 'write')
      .mockImplementation(() => true);

    createLogger('svc').info('hello');

    expect(JSON.parse(String(write.mock.calls[0][0]))).toMatchObject({
      severity: 'INFO',
      'logging.googleapis.com/labels': { logger: 'svc' },
    });
  });
});

describe('formatGcpLogLabels', () => {
  test('nests fields under the Cloud Logging labels key', () => {
    expect(formatGcpLogLabels({ logger: 'svc', requestId: 'abc' })).toEqual({
      'logging.googleapis.com/labels': { logger: 'svc', requestId: 'abc' },
    });
  });

  test('emits no labels key for an empty object', () => {
    expect(formatGcpLogLabels({})).toEqual({});
  });
});
