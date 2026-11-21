import { beforeEach, describe, expect, test, vi } from 'vitest';

import { getCacheEntries, getCacheStats } from '~/lib/middleware/network-cache';
import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/local.debug';

vi.mock('~/lib/middleware/network-cache', () => ({
  getCacheStats: vi.fn<() => unknown>(),
  getCacheEntries: vi.fn<() => unknown>(),
}));

function load() {
  return runLoader(Route, {});
}

describe('local debug route loader', () => {
  beforeEach(() => {
    vi.mocked(getCacheStats).mockReturnValue({
      size: 1,
      maxEntries: 100,
      keys: [],
      hits: 0,
      misses: 0,
      hitRate: 0,
      revalidatedNotModified: 0,
      revalidatedModified: 0,
      notModifiedRate: 0,
    });
  });

  test('splits the cache key into method and URL', async () => {
    vi.mocked(getCacheEntries).mockReturnValue([
      { key: 'GET:https://x.test/a', data: '{}', remainingTTL: 0 },
    ]);
    const result = await load();
    expect(result?.cacheEntries[0]).toMatchObject({
      method: 'GET',
      url: 'https://x.test/a',
    });
  });

  test('labels a cache key with no method as UNKNOWN', async () => {
    vi.mocked(getCacheEntries).mockReturnValue([
      { key: '', data: '{}', remainingTTL: 0 },
    ]);
    const result = await load();
    expect(result?.cacheEntries[0]).toMatchObject({
      method: 'UNKNOWN',
      url: '',
    });
  });

  test('truncates long cached bodies in the preview', async () => {
    vi.mocked(getCacheEntries).mockReturnValue([
      { key: 'GET:u', data: 'x'.repeat(60), remainingTTL: 0 },
    ]);
    const result = await load();
    expect(result?.cacheEntries[0].dataPreview).toBe(`${'x'.repeat(50)}...`);
  });

  test('shows a dash for entries without an etag', async () => {
    vi.mocked(getCacheEntries).mockReturnValue([
      { key: 'GET:u', data: '{}', remainingTTL: 0 },
    ]);
    const result = await load();
    expect(result?.cacheEntries[0].etag).toBe('—');
  });

  test('keeps the etag when present', async () => {
    vi.mocked(getCacheEntries).mockReturnValue([
      { key: 'GET:u', data: '{}', etag: 'W/"abc"', remainingTTL: 0 },
    ]);
    const result = await load();
    expect(result?.cacheEntries[0].etag).toBe('W/"abc"');
  });

  test('titles the page Network Cache Debug', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Network Cache Debug - The Blue Alliance',
    });
  });
});
