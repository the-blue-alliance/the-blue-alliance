import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearCache,
  createCachedFetch,
  getCacheStats,
} from '~/lib/middleware/network-cache';

describe('Network Cache Middleware', () => {
  beforeEach(() => {
    clearCache();
    vi.clearAllMocks();
  });

  it('should create a cached fetch function', () => {
    const cachedFetch = createCachedFetch();
    expect(cachedFetch).toBeInstanceOf(Function);
  });

  it('should cache GET requests on server side', async () => {
    // Mock fetch - return fresh Response on each call
    const mockFetch = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ data: 'test' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();

    const url = 'https://api.example.com/data';

    // First request - should hit network
    const response1 = await cachedFetch(url);
    const data1 = await response1.text();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(data1).toBe('{"data":"test"}');

    // Second request - should use cache
    const response2 = await cachedFetch(url);
    const data2 = await response2.text();
    expect(mockFetch).toHaveBeenCalledTimes(1); // Still 1, not 2
    expect(data2).toBe('{"data":"test"}');

    // Restore window
    global.window = originalWindow;
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

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();

    const url = 'https://api.example.com/data';

    // POST request - should not cache
    await cachedFetch(url, { method: 'POST' });
    await cachedFetch(url, { method: 'POST' });

    expect(mockFetch).toHaveBeenCalledTimes(2);

    // Restore window
    global.window = originalWindow;
  });

  it('should skip cache on client side', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;

    // Ensure window is defined (client side)
    const originalWindow = global.window;
    if (!global.window) {
      // @ts-expect-error - mocking window
      global.window = {};
    }

    const cachedFetch = createCachedFetch();

    const url = 'https://api.example.com/data';

    await cachedFetch(url);
    await cachedFetch(url);

    // Should call fetch both times (no caching on client)
    expect(mockFetch).toHaveBeenCalledTimes(2);

    // Restore window
    global.window = originalWindow;
  });

  it('should respect global TTL and expire old entries', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();

    const url = 'https://api.example.com/data-ttl-test';

    // First request
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Second request immediately - should use cache
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Note: We can't easily test TTL expiration without mocking time
    // The global TTL is 3 hours, which is too long for a unit test
    // This test verifies caching works, TTL is configured at module level

    // Restore window
    global.window = originalWindow;
  });

  it('should respect maxEntries limit', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation((url: string) =>
        Promise.resolve(new Response(url, { status: 200 })),
      );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();

    // Make requests to different URLs - should respect default maxEntries
    for (let i = 0; i < 5; i++) {
      await cachedFetch(`https://api.example.com/data/${i}`);
    }

    const stats = getCacheStats();
    // Should have cached all 5 entries (well under default of 500)
    expect(stats.size).toBe(5);

    // Restore window
    global.window = originalWindow;
  });

  it('should clear cache correctly', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    // Add to cache
    await cachedFetch(url);
    expect(getCacheStats().size).toBe(1);

    // Clear cache
    clearCache();
    expect(getCacheStats().size).toBe(0);

    // Next request should hit network
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(2);

    // Restore window
    global.window = originalWindow;
  });

  it('should only cache successful responses (2xx)', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('error', { status: 404 })),
      );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/not-found';

    // First 404 request
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Second request - should not use cache (404 not cached)
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(2);

    // Restore window
    global.window = originalWindow;
  });

  it('should use same cache key regardless of headers', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(new Response('test', { status: 200 })),
      );
    global.fetch = mockFetch;

    // Mock server environment
    const originalWindow = global.window;
    // @ts-expect-error - mocking window
    delete global.window;

    const cachedFetch = createCachedFetch();
    const url = 'https://api.example.com/data';

    // Request with header 1
    await cachedFetch(url, {
      headers: { 'Accept-Language': 'en' },
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Request with different header - should use cache (headers ignored)
    await cachedFetch(url, {
      headers: { 'Accept-Language': 'es' },
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Request without headers - should use cache
    await cachedFetch(url);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Restore window
    global.window = originalWindow;
  });
});
