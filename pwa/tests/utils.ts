import { test } from '@playwright/test';

/**
 * Skips the current test or describe block if a valid TBA API key is not configured.
 * Use this in tests that require API access to load data.
 *
 * @example
 * test.beforeAll(skipWithoutApiKey);
 */
export function skipWithoutApiKey() {
  const apiKey = process.env.VITE_TBA_API_READ_KEY;
  const hasValidApiKey = apiKey && apiKey !== '' && apiKey !== 'myKey';

  test.skip(
    !hasValidApiKey,
    'Skipping test: VITE_TBA_API_READ_KEY not configured (requires API access)',
  );
}
