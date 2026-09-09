import * as Sentry from '@sentry/tanstackstart-react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearCache,
  createCachedFetch,
  getCacheEntries,
  getCacheStats,
} from '~/lib/middleware/network-cache';

const loggerMocks = vi.hoisted(() => ({
  debug: vi.fn<(bindings: object, message: string) => void>(),
  warn: vi.fn<(bindings: object, message: string) => void>(),
}));

vi.mock('@sentry/tanstackstart-react', () => ({
  metrics: {
    count: vi.fn<typeof Sentry.metrics.count>(),
    distribution: vi.fn<typeof Sentry.metrics.distribution>(),
    gauge: vi.fn<typeof Sentry.metrics.gauge>(),
  },
}));

vi.mock('~/lib/logger', () => ({
  createLogger: () => loggerMocks,
}));

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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ data: 'test' }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'public, max-age=61',
          },
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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
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
      .fn<typeof fetch>()
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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
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

  it('should warn when Cache-Control is missing', async () => {
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
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
    const url = 'https://api.example.com/no-cache-control-warning';

    await cachedFetch(url);

    expect(loggerMocks.warn).toHaveBeenCalledWith(
      { method: 'GET', url },
      'No usable Cache-Control max-age; falling back to default TTL',
    );
  });

  it('should respect maxEntries limit', async () => {
    const mockFetch = vi.fn<typeof fetch>().mockImplementation((url) =>
      Promise.resolve(
        new Response(url instanceof Request ? url.url : String(url), {
          status: 200,
          headers: { 'Cache-Control': 'public, max-age=61' },
        }),
      ),
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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
      Promise.resolve(
        new Response('test', {
          status: 200,
          headers: { 'Cache-Control': 'public, max-age=61' },
        }),
      ),
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

  it('serves a stale entry immediately and revalidates in the background', async () => {
    let body = 'v1';
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
      Promise.resolve(
        new Response(body, {
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
    const url = 'https://api.example.com/swr';

    const first = await (await cachedFetch(url)).text();
    expect(first).toBe('v1');
    expect(mockFetch).toHaveBeenCalledTimes(1);

    body = 'v2';
    await new Promise((resolve) => setTimeout(resolve, 1100));

    const stale = await (await cachedFetch(url)).text();
    expect(stale).toBe('v1');
    expect(Sentry.metrics.count).toHaveBeenCalledWith(
      'network.cache.stale',
      1,
      expect.anything(),
    );

    await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));

    const fresh = await (await cachedFetch(url)).text();
    expect(fresh).toBe('v2');
  });

  it('should only cache successful responses (2xx)', async () => {
    const mockFetch = vi
      .fn<typeof fetch>()
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
    const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
      Promise.resolve(
        new Response('test', {
          status: 200,
          headers: { 'Cache-Control': 'public, max-age=61' },
        }),
      ),
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

  describe('hit rate tracking', () => {
    function mockOkFetch() {
      const mockFetch = vi.fn<typeof fetch>().mockImplementation(() =>
        Promise.resolve(
          new Response('{"data":"test"}', {
            status: 200,
            headers: { 'Cache-Control': 'public, max-age=61' },
          }),
        ),
      );
      global.fetch = mockFetch;
      return mockFetch;
    }

    it('counts a miss then a hit', async () => {
      mockOkFetch();
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      await cachedFetch(url);
      await cachedFetch(url);

      const stats = getCacheStats();
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBe(0.5);
    });

    it('reports a zero hit rate with no traffic', () => {
      expect(getCacheStats()).toMatchObject({
        hits: 0,
        misses: 0,
        hitRate: 0,
      });
    });

    it('computes the hit rate over repeated requests', async () => {
      mockOkFetch();
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      for (let i = 0; i < 4; i++) {
        await cachedFetch(url);
      }

      const stats = getCacheStats();
      expect(stats.hits).toBe(3);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBe(0.75);
    });

    it('does not move counters for non-cacheable methods', async () => {
      mockOkFetch();
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      await cachedFetch(url, { method: 'POST' });
      await cachedFetch(url, { method: 'POST' });

      expect(getCacheStats()).toMatchObject({ hits: 0, misses: 0 });
    });

    it('does not move counters on the client side', async () => {
      mockOkFetch();
      if (!global.window) {
        // @ts-expect-error - mocking window
        global.window = {};
      }

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      await cachedFetch(url);
      await cachedFetch(url);

      expect(getCacheStats()).toMatchObject({ hits: 0, misses: 0 });
    });

    it('counts a 404 as a miss, never a hit', async () => {
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(new Response('error', { status: 404 })),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/not-found';

      await cachedFetch(url);
      await cachedFetch(url);

      expect(getCacheStats()).toMatchObject({ hits: 0, misses: 2 });
    });

    it('resets counters on clearCache', async () => {
      mockOkFetch();
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      await cachedFetch(url);
      await cachedFetch(url);
      clearCache();

      expect(getCacheStats()).toMatchObject({
        hits: 0,
        misses: 0,
        hitRate: 0,
      });
    });

    it('emits Sentry counters only for real server-side cache accesses', async () => {
      mockOkFetch();
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/data';

      await cachedFetch(url);
      await cachedFetch(url);
      await cachedFetch(url, { method: 'POST' });

      expect(Sentry.metrics.count).toHaveBeenCalledWith(
        'network.cache.miss',
        1,
        {
          attributes: { client_platform: 'pwa' },
        },
      );
      expect(Sentry.metrics.count).toHaveBeenCalledWith(
        'network.cache.hit',
        1,
        {
          attributes: { client_platform: 'pwa' },
        },
      );
      expect(Sentry.metrics.count).toHaveBeenCalledTimes(2);
    });
  });

  describe('ETag revalidation', () => {
    const sleep = (ms: number) =>
      new Promise((resolve) => setTimeout(resolve, ms));

    function respond(
      body: string,
      { etag, maxAge = 1 }: { etag?: string; maxAge?: number } = {},
    ): Response {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${maxAge}`,
      };
      if (etag) {
        headers.ETag = etag;
      }
      return new Response(body, { status: 200, headers });
    }

    function notModified(headers: Record<string, string> = {}): Response {
      return {
        status: 304,
        ok: false,
        headers: new Headers(headers),
        text: () => Promise.resolve(''),
      } as unknown as Response;
    }

    it('stores the ETag and sends If-None-Match once stale', async () => {
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(respond('v1', { etag: '"abc"' })),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/etag';

      await cachedFetch(url);
      expect(getCacheEntries()[0]?.etag).toBe('"abc"');

      await sleep(1100);
      await cachedFetch(url);
      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));

      const headers = new Headers(mockFetch.mock.calls[1]?.[1]?.headers);
      expect(headers.get('If-None-Match')).toBe('"abc"');
    });

    it('serves the cached body and refreshes TTL on a 304', async () => {
      let isNotModified = false;
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(
            isNotModified
              ? notModified({ 'Cache-Control': 'public, max-age=60' })
              : respond('body-v1', { etag: '"v1"' }),
          ),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/not-modified';

      await cachedFetch(url);
      await sleep(1100);
      isNotModified = true;

      const stale = await (await cachedFetch(url)).text();
      expect(stale).toBe('body-v1');

      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));
      await vi.waitFor(() =>
        expect(getCacheEntries()[0]?.remainingTTL ?? 0).toBeGreaterThan(30_000),
      );
      const revalidated = await (await cachedFetch(url)).text();
      expect(revalidated).toBe('body-v1');
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(Sentry.metrics.count).toHaveBeenCalledWith(
        'network.cache.revalidate.not_modified',
        1,
        expect.anything(),
      );
      expect(getCacheStats()).toMatchObject({
        revalidatedNotModified: 1,
        revalidatedModified: 0,
        notModifiedRate: 1,
      });
    });

    it('tracks the not-modified rate across mixed revalidations', async () => {
      let mode: '200' | '304' = '200';
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(
            mode === '304'
              ? notModified({ 'Cache-Control': 'public, max-age=1' })
              : respond('v1', { etag: '"v1"', maxAge: 1 }),
          ),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/rate';

      await cachedFetch(url);

      await sleep(1100);
      mode = '304';
      await cachedFetch(url);
      await vi.waitFor(() =>
        expect(getCacheStats().revalidatedNotModified).toBe(1),
      );

      await sleep(1100);
      mode = '200';
      await cachedFetch(url);
      await vi.waitFor(() =>
        expect(getCacheStats().revalidatedModified).toBe(1),
      );

      expect(getCacheStats().notModifiedRate).toBe(0.5);
    });

    it('reuses the original freshness window when a 304 omits Cache-Control', async () => {
      let isNotModified = false;
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(
            isNotModified
              ? notModified()
              : respond('body-v1', { etag: '"v1"', maxAge: 3 }),
          ),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/no-cc-304';

      await cachedFetch(url);
      await sleep(3100);
      isNotModified = true;
      await cachedFetch(url);

      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));
      await vi.waitFor(() =>
        expect(getCacheEntries()[0]?.remainingTTL ?? 0).toBeGreaterThan(1000),
      );
      expect(getCacheEntries()[0]?.remainingTTL).toBeLessThan(4000);
    });

    it('replaces the body and ETag when revalidation returns a 200', async () => {
      let second = false;
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(
            second
              ? respond('v2', { etag: '"v2"' })
              : respond('v1', { etag: '"v1"' }),
          ),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/changed';

      await cachedFetch(url);
      await sleep(1100);
      second = true;
      await cachedFetch(url);

      await vi.waitFor(() => expect(getCacheEntries()[0]?.data).toBe('v2'));
      expect(getCacheEntries()[0]?.etag).toBe('"v2"');
      expect(Sentry.metrics.count).toHaveBeenCalledWith(
        'network.cache.revalidate.modified',
        1,
        expect.anything(),
      );
    });

    it('revalidates unconditionally when no ETag was stored', async () => {
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() => Promise.resolve(respond('v1')));
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/no-etag';

      await cachedFetch(url);
      await sleep(1100);
      await cachedFetch(url);
      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));

      const headers = new Headers(mockFetch.mock.calls[1]?.[1]?.headers);
      expect(headers.get('If-None-Match')).toBeNull();
    });

    it('treats max-age=0 as stale on the next read', async () => {
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
          Promise.resolve(respond('v1', { etag: '"v1"', maxAge: 0 })),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/no-store';

      await cachedFetch(url);
      await sleep(10);
      await cachedFetch(url);
      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));
      expect(Sentry.metrics.count).toHaveBeenCalledWith(
        'network.cache.stale',
        1,
        expect.anything(),
      );
    });

    it('collapses concurrent cold misses to one origin request', async () => {
      const mockFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(
          () =>
            new Promise((resolve) =>
              setTimeout(() => resolve(respond('shared', { maxAge: 60 })), 50),
            ),
        );
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/stampede';

      const [a, b] = await Promise.all([cachedFetch(url), cachedFetch(url)]);

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(await a.text()).toBe('shared');
      expect(await b.text()).toBe('shared');
    });

    it('refetches unconditionally when a 304 arrives with no cached body', async () => {
      let calls = 0;
      const mockFetch = vi.fn<typeof fetch>().mockImplementation(() => {
        calls++;
        return Promise.resolve(
          calls === 1 ? notModified() : respond('recovered', { maxAge: 60 }),
        );
      });
      global.fetch = mockFetch;
      mockServerEnvironment();

      const cachedFetch = createCachedFetch();
      const url = 'https://api.example.com/orphan-304';

      const body = await (await cachedFetch(url)).text();
      expect(body).toBe('recovered');
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});
