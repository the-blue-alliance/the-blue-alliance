import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearCache,
  createCachedFetch,
  getCacheEntries,
  getCacheStats,
} from '~/lib/middleware/network-cache';

describe('Network Cache Middleware', () => {
  let originalWindow: typeof globalThis.window;

  beforeEach(() => {
    clearCache();
    vi.clearAllMocks();
    originalWindow = global.window;
  });

  afterEach(() => {
    global.window = originalWindow;
  });

  function mockServerEnvironment() {
    // @ts-expect-error - mocking window
    delete global.window;
  }

  it('should create a cached fetch function', () => {
    const cachedFetch = createCachedFetch();
    expect(cachedFetch).toBeInstanceOf(Function);
  });

  it('should cache GET requests on server side', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ data: 'test' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    const response1 = await cachedFetch(url);
    const data1 = await response1.text();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(data1).toBe('{"data":"test"}');

    const response2 = await cachedFetch(url);
    const data2 = await response2.text();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(data2).toBe('{"data":"test"}');
  });

  it('should not cache non-GET requests', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ success: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    await cachedFetch(url, { method: 'POST' });
    await cachedFetch(url, { method: 'POST' });

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should skip cache on client side and not grow the LRU', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;

    if (!global.window) {
      // @ts-expect-error - mocking window
      global.window = {};
    }

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    await cachedFetch(url);
    await cachedFetch(url);

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(getCacheStats().size).toBe(0);
  });

  it('should respect Cache-Control max-age for TTL', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response('cached-body', {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'public, max-age=1',
          },
        }),
      ),
    );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/max-age-test';

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Still within max-age — serve from cache
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const entries = getCacheEntries();
    expect(entries).toHaveLength(1);
    // max-age=1 → ~1000ms remaining (lru-cache may report slightly above)
    expect(entries[0]?.remainingTTL).toBeGreaterThan(0);
    expect(entries[0]?.remainingTTL).toBeLessThan(2000);
  });

  it('should fall back to default TTL when Cache-Control is missing', async () => {
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response('no-cc', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/no-cache-control';

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(getCacheStats().size).toBe(1);

    // Within the default 61s TTL window — still cached
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const entries = getCacheEntries();
    expect(entries).toHaveLength(1);
    // Default fallback is 61s — longer than a 1s max-age entry
    expect(entries[0]?.remainingTTL).toBeGreaterThan(1000);
    expect(entries[0]?.remainingTTL).toBeLessThanOrEqual(62_000);
  });

  it('should respect maxEntries limit', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation((url: string) =>
        Promise.resolve(new Response(url, { status: 200 })),
      );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();

    for (let i = 0; i < 5; i++) {
      await cachedFetch(`https://api.example.com/data/${i}`);
    }

    const stats = getCacheStats();
    expect(stats.size).toBe(5);
  });

  it('should clear cache correctly', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    await cachedFetch(url);
    expect(getCacheStats().size).toBe(1);

    clearCache();
    expect(getCacheStats().size).toBe(0);

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should only cache successful responses (2xx)', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('error', { status: 404 })),
      );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/not-found';

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should use same cache key regardless of headers', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;
    mockServerEnvironment();

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    await cachedFetch(url, {
      headers: { 'Accept-Language': 'en' },
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    await cachedFetch(url, {
      headers: { 'Accept-Language': 'es' },
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});
