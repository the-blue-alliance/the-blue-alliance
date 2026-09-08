/**
 * SSR-only network cache middleware for TBA API requests.
 *
 * Per-process in-memory LRU shared across users on a given SSR instance.
 * Safe only because TBA read data is public and `X-TBA-Auth-Key` is a single
 * shared read key — do not use this for user-private responses. If per-user
 * auth keys ever land, cache keys must include the auth identity (or stop
 * caching those requests).
 *
 * Freshness comes from the origin's `Cache-Control: max-age`. Once an entry is
 * stale it is revalidated with `If-None-Match` against the stored `ETag`: a 304
 * refreshes the entry's TTL without re-transferring the body. APIv3 emits a
 * strong `ETag` on every 200 and has a fast path that answers conditional
 * requests with 304 without running the handler.
 *
 * Installed only on the server via `client.setConfig` in `__root.tsx`. Client
 * freshness is owned by React Query `staleTime`; this must not run in the
 * browser as a second TTL under Query.
 */
import { metrics } from '@sentry/tanstackstart-react';
import ccParser from 'cache-control-parser';
import { LRUCache } from 'lru-cache';

import { createLogger, secondsToMilliseconds } from '~/lib/utils';

interface CacheEntry {
  body: string;
  etag?: string;
  /** Freshness window the origin declared, reused when a 304 omits its own. */
  ttlMs: number;
}

/**
 * Cap kept deliberately modest: heavy pages (e.g. district stats) can fan out
 * 20–40 entries and benefit from headroom, but each SSR instance holds the
 * full LRU in memory — raising this fights F1 OOM pressure (see #9984).
 */
const CACHE_MAX_ENTRIES = 300;
/** Fallback when the origin omits Cache-Control / max-age — matches TBA API max-age. */
const CACHE_TTL = secondsToMilliseconds(61);

/**
 * Global singleton LRU cache - shared across all SSR sessions on this process
 */
const cache = new LRUCache<string, CacheEntry>({
  max: CACHE_MAX_ENTRIES,
  ttl: CACHE_TTL,
  allowStale: true,
  noDeleteOnStaleGet: true,
});

interface OriginResult {
  body: string;
  status: number;
}

/**
 * In-flight origin requests keyed by cache key. Shared by the stale
 * revalidation path (fire-and-forget) and cold misses (awaited), so concurrent
 * renders of the same key collapse to one upstream request.
 */
const inFlight = new Map<string, Promise<OriginResult>>();

let hits = 0;
let misses = 0;
let revalidatedNotModified = 0;
let revalidatedModified = 0;

interface NetworkCacheConfig {
  /**
   * Methods to cache (only these HTTP methods will be cached)
   * @default ['GET']
   */
  cacheableMethods?: string[];
}

const logger = createLogger('network-cache');

function countMetric(name: string): void {
  metrics.count(name, 1, { attributes: { client_platform: 'pwa' } });
}

/**
 * Store an entry, honoring its freshness window. `lru-cache` treats a `ttl` of 0
 * as "never expire", so `max-age=0` is clamped to 1ms — effectively stale on the
 * next read, which is the intent.
 */
function setEntry(cacheKey: string, entry: CacheEntry): void {
  cache.set(cacheKey, entry, { ttl: Math.max(entry.ttlMs, 1) });
}

/**
 * Generate cache key from request.
 * Keyed on METHOD:url only — fine today with one shared read key; not safe
 * if responses ever vary by auth header.
 */
function generateCacheKey(url: string, options: RequestInit = {}): string {
  const method = options.method?.toUpperCase() || 'GET';
  return `${method}:${url}`;
}

/**
 * TTL in ms from a Cache-Control header, or undefined when absent. `max-age=0`
 * yields 0 (stale immediately), not undefined.
 */
function ttlFromCacheControl(header: string | null): number | undefined {
  if (!header) {
    return undefined;
  }
  const parsed = ccParser.parse(header);
  return parsed['max-age'] === undefined
    ? undefined
    : secondsToMilliseconds(parsed['max-age']);
}

/**
 * Create a caching fetch function (SSR-only; no-ops if invoked in the browser)
 */
export function createCachedFetch(
  config: NetworkCacheConfig = {},
): typeof fetch {
  const cacheableMethods = config.cacheableMethods || ['GET'];

  return async function cachedFetch(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    // Defense in depth: never cache in the browser even if setConfig leaks.
    if (typeof window !== 'undefined') {
      return fetch(input, init);
    }

    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const method = init?.method?.toUpperCase() || 'GET';

    // Only cache specified methods (default: GET)
    if (!cacheableMethods.includes(method)) {
      logger.debug(
        {
          method,
          url,
        },
        'Skipping cache for non-cacheable method',
      );

      return fetch(input, init);
    }

    const cacheKey = generateCacheKey(url, init);

    const cachedEntry = cache.get(cacheKey, { allowStale: true });
    const isFresh =
      cachedEntry !== undefined && cache.getRemainingTTL(cacheKey) > 0;

    if (cachedEntry !== undefined && isFresh) {
      hits++;
      countMetric('network.cache.hit');
      logger.debug({ method, url }, 'Cache HIT');
      return jsonResponse(cachedEntry.body);
    }

    if (cachedEntry !== undefined) {
      // Stale-while-revalidate: serve the stale body now, refresh off the
      // request's critical path. Keeps SSR TTFB flat when an entry has just
      // expired instead of blocking on an origin round-trip.
      hits++;
      countMetric('network.cache.hit');
      countMetric('network.cache.stale');
      logger.debug(
        { method, url },
        'Cache STALE - serving stale, revalidating',
      );
      void startOriginRequest(
        input,
        init,
        cacheKey,
        method,
        url,
        cachedEntry,
      ).catch(() => undefined);
      return jsonResponse(cachedEntry.body);
    }

    misses++;
    countMetric('network.cache.miss');
    logger.debug({ method, url }, 'Outbound request');

    const result = await startOriginRequest(
      input,
      init,
      cacheKey,
      method,
      url,
      undefined,
    );
    return new Response(result.body, {
      status: result.status,
      headers: { 'Content-Type': 'application/json' },
    });
  };
}

function jsonResponse(body: string): Response {
  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Kick off (or join) the single in-flight origin request for `cacheKey`.
 */
function startOriginRequest(
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  cacheKey: string,
  method: string,
  url: string,
  entry: CacheEntry | undefined,
): Promise<OriginResult> {
  const existing = inFlight.get(cacheKey);
  if (existing) {
    return existing;
  }

  const pending = fetchAndStore(
    input,
    init,
    cacheKey,
    method,
    url,
    entry,
  ).catch((error: unknown) => {
    logger.error({ method, url, error }, 'Request failed');
    throw error;
  });
  inFlight.set(cacheKey, pending);
  void pending.catch(() => undefined).finally(() => inFlight.delete(cacheKey));
  return pending;
}

function conditionalInit(
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  etag: string,
): RequestInit {
  const headers = new Headers(
    init?.headers ?? (input instanceof Request ? input.headers : undefined),
  );
  headers.set('If-None-Match', etag);
  return { ...init, headers };
}

/**
 * Fetch from the origin (conditionally when a stored ETag exists), update the
 * cache, and return the body to serve. Used for both cache misses and
 * background stale revalidation.
 */
async function fetchAndStore(
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  cacheKey: string,
  method: string,
  url: string,
  entry: CacheEntry | undefined,
): Promise<OriginResult> {
  const revalidating = entry !== undefined;
  const response = await fetch(
    input,
    entry?.etag ? conditionalInit(input, init, entry.etag) : init,
  );

  if (response.status === 304) {
    const known = entry ?? cache.get(cacheKey, { allowStale: true });
    if (!known) {
      // Entry vanished mid-flight — refetch unconditionally.
      return fetchAndStore(input, init, cacheKey, method, url, undefined);
    }
    const ttlMs =
      ttlFromCacheControl(response.headers.get('cache-control')) ?? known.ttlMs;
    setEntry(cacheKey, {
      body: known.body,
      etag: response.headers.get('etag') ?? known.etag,
      ttlMs,
    });
    revalidatedNotModified++;
    countMetric('network.cache.revalidate.not_modified');
    logger.debug({ method, url, ttlMs }, 'Revalidated (304)');
    return { body: known.body, status: 200 };
  }

  if (response.ok && response.status >= 200 && response.status < 300) {
    const body = await response.text();
    const cacheControl = response.headers.get('cache-control');
    const parsedTtl = ttlFromCacheControl(cacheControl);
    if (parsedTtl === undefined) {
      logger.warn(
        { method, url },
        'No usable Cache-Control max-age; falling back to default TTL',
      );
    }
    const ttlMs = parsedTtl ?? CACHE_TTL;
    setEntry(cacheKey, {
      body,
      etag: response.headers.get('etag') ?? undefined,
      ttlMs,
    });
    if (revalidating) {
      revalidatedModified++;
      countMetric('network.cache.revalidate.modified');
    }
    logger.debug({ method, url, ttlMs }, 'Cached response');
    return { body, status: response.status };
  }

  return { body: await response.text(), status: response.status };
}

/**
 * Clear the cache
 */
export function clearCache(): void {
  cache.clear();
  inFlight.clear();
  hits = 0;
  misses = 0;
  revalidatedNotModified = 0;
  revalidatedModified = 0;
  logger.debug('Cache cleared');
}

/**
 * Get cache statistics
 */
export function getCacheStats(): {
  size: number;
  maxEntries: number;
  keys: string[];
  hits: number;
  misses: number;
  hitRate: number;
  revalidatedNotModified: number;
  revalidatedModified: number;
  notModifiedRate: number;
} {
  const total = hits + misses;
  const revalidations = revalidatedNotModified + revalidatedModified;
  return {
    size: cache.size,
    maxEntries: CACHE_MAX_ENTRIES,
    keys: Array.from(cache.keys()),
    hits,
    misses,
    hitRate: total === 0 ? 0 : hits / total,
    revalidatedNotModified,
    revalidatedModified,
    notModifiedRate:
      revalidations === 0 ? 0 : revalidatedNotModified / revalidations,
  };
}

/**
 * Get cache entries with their data
 */
export function getCacheEntries(): Array<{
  key: string;
  data: string;
  etag?: string;
  remainingTTL: number;
}> {
  const entries: Array<{
    key: string;
    data: string;
    etag?: string;
    remainingTTL: number;
  }> = [];

  cache.forEach((value, key) => {
    const remainingTTL = cache.getRemainingTTL(key);
    entries.push({ key, data: value.body, etag: value.etag, remainingTTL });
  });

  return entries;
}
