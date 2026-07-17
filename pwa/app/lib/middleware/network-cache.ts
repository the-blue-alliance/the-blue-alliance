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
 */
import ccParser from 'cache-control-parser';
import { LRUCache } from 'lru-cache';

import { createLogger, secondsToMilliseconds } from '~/lib/utils';

type CacheEntry = string;

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
});

interface NetworkCacheConfig {
  /**
   * Methods to cache (only these HTTP methods will be cached)
   * @default ['GET']
   */
  cacheableMethods?: string[];
}

const logger = createLogger('network-cache');

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

    // Check cache
    const cachedData = cache.get(cacheKey);
    if (cachedData) {
      logger.debug(
        {
          method,
          url,
        },
        'Cache HIT',
      );
      return new Response(cachedData, {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Cache miss or expired - fetch from network
    logger.debug(
      {
        method,
        url,
      },
      'Outbound request',
    );

    try {
      const response = await fetch(input, init);

      // Only cache successful responses
      if (response.ok && response.status >= 200 && response.status < 300) {
        // Read response body as text to avoid clone() issues
        const data = await response.text();

        // Get TTL from Cache-Control header, fall back to default
        const cacheControl = response.headers.get('cache-control');
        if (!cacheControl) {
          logger.warn(
            {
              method,
              url,
            },
            'No Cache-Control header found; falling back to default TTL',
          );
          cache.set(cacheKey, data, { ttl: CACHE_TTL });
        } else {
          const ttl = ccParser.parse(cacheControl);

          if (!ttl['max-age']) {
            logger.warn(
              {
                method,
                url,
              },
              'No max-age found in Cache-Control header; falling back to default TTL',
            );
            cache.set(cacheKey, data, { ttl: CACHE_TTL });
          } else {
            const ttlMs = secondsToMilliseconds(ttl['max-age']);
            logger.debug(
              {
                method,
                url,
                ttlMs,
              },
              'Cached response with max-age',
            );
            cache.set(cacheKey, data, { ttl: ttlMs });
          }
        }

        // Return a new Response with the cached data
        return new Response(data, {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      return response;
    } catch (error) {
      logger.error(
        {
          method,
          url,
          error,
        },
        'Request failed',
      );
      throw error;
    }
  };
}

/**
 * Clear the cache
 */
export function clearCache(): void {
  cache.clear();
  logger.debug('Cache cleared');
}

/**
 * Get cache statistics
 */
export function getCacheStats(): {
  size: number;
  maxEntries: number;
  keys: string[];
} {
  return {
    size: cache.size,
    maxEntries: CACHE_MAX_ENTRIES,
    keys: Array.from(cache.keys()),
  };
}

/**
 * Get cache entries with their data
 */
export function getCacheEntries(): Array<{
  key: string;
  data: string;
  remainingTTL: number;
}> {
  const entries: Array<{ key: string; data: string; remainingTTL: number }> =
    [];

  cache.forEach((value, key) => {
    const remainingTTL = cache.getRemainingTTL(key);
    entries.push({ key, data: value, remainingTTL });
  });

  return entries;
}
