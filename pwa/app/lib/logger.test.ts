import { describe, expect, test, vi } from 'vitest';

import { createLogger } from '~/lib/logger';

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
