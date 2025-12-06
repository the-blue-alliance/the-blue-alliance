/**
 * Network cache middleware for API requests
 *
 * Implements an in-memory KV store to cache API responses across sessions.
 * Includes logging to track cache hits and outbound requests.
 */

interface CacheEntry {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: string;
  timestamp: number;
}

interface NetworkCacheConfig {
  /**
   * Maximum number of entries to store in cache
   * @default 500
   */
  maxEntries?: number;

  /**
   * Time-to-live for cache entries in milliseconds
   * @default 300000 (5 minutes)
   */
  ttl?: number;

  /**
   * Enable debug logging
   * @default false
   */
  debug?: boolean;

  /**
   * Methods to cache (only these HTTP methods will be cached)
   * @default ['GET']
   */
  cacheableMethods?: string[];
}

/**
 * In-memory cache store shared across all sessions
 * Using a Map instead of LRUCache to avoid clone() issues
 */
const cache = new Map<string, CacheEntry>();

/**
 * LRU tracking - keeps order of access
 */
const accessOrder: string[] = [];

/**
 * Default configuration
 */
const defaultConfig: Required<NetworkCacheConfig> = {
  maxEntries: 500,
  ttl: 10800000, // 3 hours
  debug: false,
  cacheableMethods: ['GET'],
};

/**
 * Generate cache key from request
 */
function generateCacheKey(url: string, options: RequestInit = {}): string {
  const method = options.method?.toUpperCase() || 'GET';
  const headers = options.headers;
  let headersStr = '';

  if (headers) {
    const headerEntries: string[] = [];

    if (headers instanceof Headers) {
      headers.forEach((value, key) => {
        // Exclude auth and cache-control headers from cache key
        if (
          !key.toLowerCase().startsWith('x-tba-auth') &&
          key.toLowerCase() !== 'cache-control'
        ) {
          headerEntries.push(`${key}:${value}`);
        }
      });
    } else if (typeof headers === 'object') {
      // Handle plain object or array of tuples
      const headerObj: Record<string, string> = Array.isArray(headers)
        ? Object.fromEntries(headers)
        : headers;

      Object.entries(headerObj).forEach(([key, value]) => {
        if (
          !key.toLowerCase().startsWith('x-tba-auth') &&
          key.toLowerCase() !== 'cache-control'
        ) {
          headerEntries.push(`${key}:${value}`);
        }
      });
    }

    headersStr = headerEntries.sort().join('|');
  }

  return `${method}:${url}${headersStr ? ':' + headersStr : ''}`;
}

/**
 * Update LRU tracking
 */
function updateAccessOrder(key: string, maxEntries: number): void {
  // Remove existing entry if present
  const existingIndex = accessOrder.indexOf(key);
  if (existingIndex > -1) {
    accessOrder.splice(existingIndex, 1);
  }

  // Add to end (most recently used)
  accessOrder.push(key);

  // Evict oldest entries if we exceed max
  while (accessOrder.length > maxEntries) {
    const oldestKey = accessOrder.shift();
    if (oldestKey) {
      cache.delete(oldestKey);
    }
  }
}

/**
 * Check if entry is expired
 */
function isExpired(entry: CacheEntry, ttl: number): boolean {
  return Date.now() - entry.timestamp > ttl;
}

/**
 * Log cache activity
 */
function log(message: string, debug: boolean = false): void {
  const timestamp = new Date().toISOString();
  if (debug) {
    // eslint-disable-next-line no-console
    console.log(`[NetworkCache ${timestamp}] ${message}`);
  } else {
    // eslint-disable-next-line no-console
    console.log(`[NetworkCache] ${message}`);
  }
}

/**
 * Convert Response to CacheEntry
 */
async function responseToCacheEntry(response: Response): Promise<CacheEntry> {
  const headers: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    headers[key] = value;
  });

  // Read body as text to avoid clone() issues
  const body = await response.text();

  return {
    status: response.status,
    statusText: response.statusText,
    headers,
    body,
    timestamp: Date.now(),
  };
}

/**
 * Convert CacheEntry to Response
 */
function cacheEntryToResponse(entry: CacheEntry): Response {
  const headers = new Headers(entry.headers);

  return new Response(entry.body, {
    status: entry.status,
    statusText: entry.statusText,
    headers,
  });
}

/**
 * Create a caching fetch function
 */
export function createCachedFetch(
  config: NetworkCacheConfig = {},
): typeof fetch {
  const finalConfig = { ...defaultConfig, ...config };

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
    if (!finalConfig.cacheableMethods.includes(method)) {
      if (finalConfig.debug) {
        log(`Skipping cache for ${method} ${url}`, finalConfig.debug);
      }
      return fetch(input, init);
    }

    // Check if running on server
    const isServer = typeof window === 'undefined';
    if (!isServer) {
      // Don't cache on client - only server-side
      if (finalConfig.debug) {
        log(`Client-side request, skipping cache: ${url}`, finalConfig.debug);
      }
      return fetch(input, init);
    }

    const cacheKey = generateCacheKey(url, init);

    // Check cache
    const cachedEntry = cache.get(cacheKey);
    if (cachedEntry && !isExpired(cachedEntry, finalConfig.ttl)) {
      updateAccessOrder(cacheKey, finalConfig.maxEntries);
      log(`✓ Cache HIT: ${method} ${url}`);
      return cacheEntryToResponse(cachedEntry);
    }

    // Cache miss or expired - fetch from network
    log(`→ Outbound request: ${method} ${url}`);

    try {
      const response = await fetch(input, init);

      // Only cache successful responses
      if (response.ok && response.status >= 200 && response.status < 300) {
        // Read response body immediately to avoid clone() issues
        const entry = await responseToCacheEntry(response);

        cache.set(cacheKey, entry);
        updateAccessOrder(cacheKey, finalConfig.maxEntries);

        if (finalConfig.debug) {
          log(`Cached response for: ${method} ${url}`, finalConfig.debug);
        }

        // Return a new Response with the cached body
        return cacheEntryToResponse(entry);
      }

      return response;
    } catch (error) {
      log(`✗ Request failed: ${method} ${url} - ${error}`);
      throw error;
    }
  };
}

/**
 * Clear the cache
 */
export function clearCache(): void {
  cache.clear();
  accessOrder.length = 0;
  log('Cache cleared');
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
    maxEntries: defaultConfig.maxEntries,
    keys: Array.from(cache.keys()),
  };
}
