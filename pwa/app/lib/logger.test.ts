import { afterEach, describe, expect, test } from 'vitest';

import { createLogger } from '~/lib/logger';

const originalNodeEnv = process.env.NODE_ENV;
const originalLogLevel = process.env.LOG_LEVEL;

afterEach(() => {
  process.env.NODE_ENV = originalNodeEnv;
  process.env.LOG_LEVEL = originalLogLevel;
});

describe('createLogger', () => {
  test('defaults to info in production, so debug hot-path logs are not emitted', () => {
    process.env.NODE_ENV = 'production';
    delete process.env.LOG_LEVEL;

    const logger = createLogger('test');

    expect(logger.level).toEqual('info');
    expect(logger.isLevelEnabled('debug')).toBe(false);
    expect(logger.isLevelEnabled('warn')).toBe(true);
  });

  test('honors LOG_LEVEL so hot-path diagnostics can be turned back on', () => {
    process.env.NODE_ENV = 'production';
    process.env.LOG_LEVEL = 'debug';

    const logger = createLogger('test');

    expect(logger.level).toEqual('debug');
    expect(logger.isLevelEnabled('debug')).toBe(true);
  });
});
