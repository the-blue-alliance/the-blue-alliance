/**
 * SSR-only network cache middleware for TBA API requests.
 *
 * Per-process in-memory LRU shared across users on a given SSR instance.
 * Safe only because TBA read data is public and `X-TBA-Auth-Key` is a single
 * shared read key — do not use this for user-private responses. If per-user
 * auth keys ever land, cache keys must include the auth identity (or stop
 * caching those requests).
 *
 * Installed only on the server via `client.setConfig` in `__root.tsx`. Client
 * freshness is owned by React Query `staleTime`; this must not run in the
 * browser as a second TTL under Query.
 *
 * Entries past their freshness window are still served, immediately, while a
 * conditional revalidation runs behind the response. A `304` against the API's
 * ETag fastpath then costs no payload and no origin work. Revalidation is
 * deliberately *not* awaited: a round trip to the API is ~30ms whether it
 * returns 200 or 304, so putting it on the critical path would buy bandwidth
 * at the cost of latency, which is backwards for SSR.
 */
import * as Sentry from '@sentry/tanstackstart-react';
import ccParser from 'cache-control-parser';
import { LRUCache } from 'lru-cache';

import {
  createLogger,
  hoursToMilliseconds,
  isPastSeason,
  minutesToMilliseconds,
  seasonFromPath,
  secondsToMilliseconds,
} from '~/lib/utils';

interface CacheEntry {
  body: string;
  etag: string | undefined;
  fetchedAt: number;
  /** Upstream `max-age`, in ms. Freshness is computed here, not by the LRU. */
  freshForMs: number;
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
 * How far past its freshness window an entry may still be served.
 *
 * Past seasons are immutable, so a day-old body is the same body. Current-season
 * data can still move, so the window stays short — a stale render is corrected
 * on hydration by React Query, but only for routes whose components read from
 * the query cache.
 */
const MAX_STALE_PAST_SEASON = hoursToMilliseconds(24);
const MAX_STALE_CURRENT_SEASON = minutesToMilliseconds(5);

let hits = 0;
let misses = 0;
let staleServed = 0;
let revalidations = 0;
let evictions = 0;

/**
 * Global singleton LRU cache - shared across all SSR sessions on this process.
 *
 * Deliberately configured without a `ttl`: entries age out via `fetchedAt`
 * below, so that a stale-but-usable body stays reachable instead of being
 * dropped at the freshness boundary. The LRU's job here is bounding memory.
 */
const cache = new LRUCache<string, CacheEntry>({
  max: CACHE_MAX_ENTRIES,
  dispose: (_value, _key, reason) => {
    if (reason === 'evict') {
      evictions++;
    }
  },
});

function ageOf(entry: CacheEntry): number {
  return Date.now() - entry.fetchedAt;
}

function isFresh(entry: CacheEntry): boolean {
  return ageOf(entry) < entry.freshForMs;
}

/** Dedupes revalidations so a hot stale key fires one request, not 80. */
const inFlight = new Map<string, Promise<void>>();

interface NetworkCacheConfig {
  /**
   * Methods to cache (only these HTTP methods will be cached)
   * @default ['GET']
   */
  cacheableMethods?: string[];
}

const logger = createLogger('network-cache');

function countAccess(outcome: string) {
  Sentry.metrics.count(
    outcome === 'miss' ? 'network.cache.miss' : 'network.cache.hit',
    1,
    { attributes: { client_platform: 'pwa', outcome } },
  );
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

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') {
    return input;
  }
  return input instanceof URL ? input.toString() : input.url;
}

function maxStaleForUrl(url: string): number {
  return isPastSeason(seasonFromPath(url))
    ? MAX_STALE_PAST_SEASON
    : MAX_STALE_CURRENT_SEASON;
}

function ttlFromResponse(response: Response, url: string, method: string) {
  const cacheControl = response.headers.get('cache-control');
  if (!cacheControl) {
    logger.warn(
      { method, url },
      'No Cache-Control header found; falling back to default TTL',
    );
    return CACHE_TTL;
  }

  const parsed = ccParser.parse(cacheControl);
  if (!parsed['max-age']) {
    logger.warn(
      { method, url },
      'No max-age found in Cache-Control header; falling back to default TTL',
    );
    return CACHE_TTL;
  }

  return secondsToMilliseconds(parsed['max-age']);
}

function cachedResponse(entry: CacheEntry, status = 200): Response {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (entry.etag) {
    headers.ETag = entry.etag;
  }
  return new Response(entry.body, { status, headers });
}

/**
 * Re-issues the request with `If-None-Match` so the API's 304 fastpath can
 * answer without a body or a Datastore read. Never rejects: a failed
 * revalidation leaves the stale entry in place to be served again.
 */
function revalidate(
  cacheKey: string,
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  entry: CacheEntry,
): Promise<void> {
  const existing = inFlight.get(cacheKey);
  if (existing) {
    return existing;
  }

  const url = requestUrl(input);
  const method = init?.method?.toUpperCase() || 'GET';

  const pending = (async () => {
    const headers = new Headers(
      init?.headers ?? (input instanceof Request ? input.headers : undefined),
    );
    if (entry.etag) {
      headers.set('If-None-Match', entry.etag);
    }

    const response = await fetch(input, { ...init, headers });
    revalidations++;

    if (response.status === 304) {
      cache.set(cacheKey, {
        ...entry,
        fetchedAt: Date.now(),
        freshForMs: ttlFromResponse(response, url, method),
      });
      Sentry.metrics.count('network.cache.revalidation', 1, {
        attributes: { client_platform: 'pwa', outcome: 'not_modified' },
      });
      logger.debug({ method, url }, 'Revalidated 304');
      return;
    }

    if (response.ok) {
      cache.set(cacheKey, {
        body: await response.text(),
        etag: response.headers.get('etag') ?? undefined,
        fetchedAt: Date.now(),
        freshForMs: ttlFromResponse(response, url, method),
      });
      Sentry.metrics.count('network.cache.revalidation', 1, {
        attributes: { client_platform: 'pwa', outcome: 'replaced' },
      });
      logger.debug({ method, url }, 'Revalidated with fresh body');
    }
  })()
    .catch((error: unknown) => {
      Sentry.metrics.count('network.cache.revalidation', 1, {
        attributes: { client_platform: 'pwa', outcome: 'error' },
      });
      logger.error({ method, url, error }, 'Revalidation failed');
    })
    .finally(() => {
      inFlight.delete(cacheKey);
    });

  inFlight.set(cacheKey, pending);
  return pending;
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

    const url = requestUrl(input);
    const method = init?.method?.toUpperCase() || 'GET';

    // Only cache specified methods (default: GET)
    if (!cacheableMethods.includes(method)) {
      logger.debug({ method, url }, 'Skipping cache for non-cacheable method');

      return fetch(input, init);
    }

    const cacheKey = generateCacheKey(url, init);

    const cached = cache.get(cacheKey);

    if (cached) {
      if (isFresh(cached)) {
        hits++;
        countAccess('fresh');
        logger.debug({ method, url }, 'Cache HIT');
        return cachedResponse(cached);
      }

      const staleFor = ageOf(cached) - cached.freshForMs;
      if (staleFor <= maxStaleForUrl(url)) {
        hits++;
        staleServed++;
        countAccess('stale_served');
        logger.debug({ method, url, staleFor }, 'Cache STALE served');
        void revalidate(cacheKey, input, init, cached);
        return cachedResponse(cached);
      }

      logger.debug(
        { method, url, staleFor },
        'Cache entry too stale to serve; fetching',
      );
    }

    misses++;
    countAccess('miss');

    logger.debug({ method, url }, 'Outbound request');

    try {
      const response = await fetch(input, init);

      // Only cache successful responses
      if (response.ok && response.status >= 200 && response.status < 300) {
        // Read response body as text to avoid clone() issues
        const entry: CacheEntry = {
          body: await response.text(),
          etag: response.headers.get('etag') ?? undefined,
          fetchedAt: Date.now(),
          freshForMs: ttlFromResponse(response, url, method),
        };
        cache.set(cacheKey, entry);
        logger.debug(
          { method, url, freshForMs: entry.freshForMs },
          'Cached response',
        );

        return cachedResponse(entry, response.status);
      }

      return response;
    } catch (error) {
      logger.error({ method, url, error }, 'Request failed');
      throw error;
    }
  };
}

/**
 * Clear the cache
 */
export function clearCache(): void {
  cache.clear();
  inFlight.clear();
  hits = 0;
  misses = 0;
  staleServed = 0;
  revalidations = 0;
  evictions = 0;
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
  staleServed: number;
  revalidations: number;
  evictions: number;
} {
  const total = hits + misses;
  return {
    size: cache.size,
    maxEntries: CACHE_MAX_ENTRIES,
    keys: Array.from(cache.keys()),
    hits,
    misses,
    hitRate: total === 0 ? 0 : hits / total,
    staleServed,
    revalidations,
    evictions,
  };
}

/**
 * Get cache entries with their data
 */
export function getCacheEntries(): Array<{
  key: string;
  data: string;
  remainingTTL: number;
  etag: string | undefined;
  fetchedAt: number;
}> {
  const entries: Array<{
    key: string;
    data: string;
    remainingTTL: number;
    etag: string | undefined;
    fetchedAt: number;
  }> = [];

  cache.forEach((value, key) => {
    entries.push({
      key,
      data: value.body,
      remainingTTL: value.freshForMs - ageOf(value),
      etag: value.etag,
      fetchedAt: value.fetchedAt,
    });
  });

  return entries;
}
