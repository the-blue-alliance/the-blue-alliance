/**
 * Network cache middleware for API requests
 *
 * Implements an in-memory LRU cache to cache JSON API responses across sessions.
 * Includes logging to track cache hits and outbound requests.
 */
import ccParser from 'cache-control-parser';
import { LRUCache } from 'lru-cache';

import {
  createLogger,
  hoursToMilliseconds,
  secondsToMilliseconds,
} from '~/lib/utils';

type CacheEntry = string;

/**
 * Global cache configuration - applied to the singleton cache instance
 */
const CACHE_MAX_ENTRIES = 500;
const CACHE_TTL = hoursToMilliseconds(3);

/**
 * Global singleton LRU cache - shared across all sessions
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
 * Generate cache key from request
 */
function generateCacheKey(url: string, options: RequestInit = {}): string {
  const method = options.method?.toUpperCase() || 'GET';
  return `${method}:${url}`;
}

/**
 * Create a caching fetch function
 */
export function createCachedFetch(
  config: NetworkCacheConfig = {},
): typeof fetch {
  const cacheableMethods = config.cacheableMethods || ['GET'];

  return async function cachedFetch(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const method = init?.method?.toUpperCase() || 'GET';

    // Only cache specified methods (default: GET)
    if (!cacheableMethods.includes(method)) {
      logger.info(
        {
          method,
          url,
        },
        'Skipping cache for non-cacheable method',
      );

      return fetch(input, init);
    }

    // Check if running on server
    const isServer = typeof window === 'undefined';
    if (!isServer) {
      // Don't cache on client - only server-side
      logger.info(
        {
          method,
          url,
        },
        'Client-side request, skipping cache',
      );
      return fetch(input, init);
    }

    const cacheKey = generateCacheKey(url, init);

    // Check cache
    const cachedData = cache.get(cacheKey);
    if (cachedData) {
      logger.info(
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
    logger.info(
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
            logger.info(
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
  logger.info('Cache cleared');
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
