In order to keep costs down, TBA uses multiple [caching](https://en.wikipedia.org/wiki/Cache_(computing)) strategies. In essence, we duplicate data in a faster or cheaper storage location in order to optimize for performance or costs.

There are a number of layers of caching. Here is an overview of each, from lowest to highest level.

## NDB Caching

[This page](https://cloud.google.com/appengine/docs/standard/python/ndb/cache) describes the caching behavior of the legacy builtin NDB library, which we use.

### Per-Request Context Cache

Each HTTP request has its own "context" which is visible to only that request. Within the context, the NDB library stores every entity it sees in memory. On reads, the context cache is checked first, and if present, a value is returned. The result of reads is also written back to the context cache, for the benefit of future reads. Additionally, data being written is also duplicated in the context cache.

### Global Memcache

After the context cache, the legacy NDB library uses legacy App Engine's bundled [memcache](https://cloud.google.com/appengine/docs/legacy/standard/python/memcache) as a shared layer. Memcache is slower than the in-context cache, but still faster than reading from the datastore.

This is enabled by `app_engine_apis: true` in each service's yaml, which is what makes the bundled `google.appengine.api.memcache` client available. `MemcacheClient` (`src/backend/common/memcache.py`) wraps it.

This cache is "write through" (the NDB library automatically updates stored data when it changes), and therefore does not have an expiration time by default. Memcache has a finite capacity and evicts data under memory pressure using a [least recently used](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)) algorithm, so treat every read as a potential miss.

The main difference from the context cache is that the global cache is shared between requests, while the context cache is isolated to a single request.

> **Note:** TBA does *not* use Redis or [Cloud Memorystore](https://cloud.google.com/memorystore). It did briefly during the Python 3 migration, but moved back to bundled memcache in November 2021 (`faf5bb389`, `707e9b7d1`) when it adopted the legacy builtin NDB library. There are no Memorystore instances in the project. If you find a doc or comment referring to Redis, it is out of date.

## Application Level Query Caching

TBA's workload often involves making complex queries that span many datastore entries (for example, fetching the list of all matches at an event). The output of these queries is used by the webapp to render output pages and is also transformed into JSON objects for API representation.

The results of these queries is highly deterministic and repeatable, so it is a good candidate for caching. Plus, for large range queries, we can minimize round trips to the datastore by storing the entire response in a single object.

We have a special DB model named `CachedQueryResult` that stores the output of other DB queries. We can store both raw models, or JSON structured dictionaries for the API.

These objects do not have an expiration, so they need to be manually cleared when the data within changes. This means we need to maintain a mechanism to do so within our application code. This logic is typically handled by the `Manipulator` classes, which contain the abstractions for doing DB writes.

Two things follow from there being no expiry, and both matter:

**Entries are only written on a miss.** `CachedDatabaseQuery` writes a `CachedQueryResult` only when the lookup returned nothing (`src/backend/common/queries/database_query.py`); a cache *hit* returns the stored result without writing. So the model's `updated` field never advances past `created`, and there is no record of when an entry was last *read*. Do not treat age as a proxy for coldness — the oldest entries tend to be queries over long-finished seasons, which are both the most stable and the most expensive to recompute.

**Cache keys are versioned, and bumping a version orphans data.** The key is `{query key}:{CACHE_VERSION}:{DATABASE_QUERY_VERSION}`, with a `~dictv{major}.{subversion}` suffix for API dicts. Bumping any of those numbers changes every affected key, so the previous generation becomes permanently unreachable. It is not deleted, just stranded, and it keeps costing storage and backup space until it is purged. Left alone, old generations grew to 8.8M entries (86% of the kind) before the November 2026 purge.

### After bumping a cache version

This applies to `CachedDatabaseQuery.DATABASE_QUERY_VERSION` (every query), a query class's `CACHE_VERSION`, and a converter's `SUBVERSIONS`.

1. **Deploy the bump and confirm it is good.** The purge deletes every generation older than current, with no rollback buffer. Rolling back after a purge is safe, but the rolled-back code misses the cache until it refills.
2. **Dry run.** On `/admin/cache`, under Orphaned Entries, click **Dry Run**. Reload the page first if it has been open for more than an hour, because its CSRF token expires and the POST fails with a 400.
3. **Read the result** in the py3-tasks-io logs: search for `Orphaned CachedQueryResult dry run`. Each task logs running totals, and the last line says `finished`. Check that the `orphaned:*` counts match the generation you bumped:
   - `orphaned:db_version` for a `DATABASE_QUERY_VERSION` bump.
   - `orphaned:cache_version` or `orphaned:dict_subversion` for a per-class bump.

   `kept:undecodable` counts legacy keys whose names aren't valid UTF-8; they are always kept.
4. **Purge.** Click **Purge Orphans**. It runs the same scan and deletes as it goes.

**How long it takes:** the scan is keys-only, in a chain of tasks of 50,000 keys each on the `cache-clearing` queue. A dry run takes about 30 seconds per task. A purge takes 80–120 seconds per task, depending on how much it deletes. Over the 2.9M keys left after the 2026 cleanup, a dry run takes about 25 minutes and a purge about 1.5 hours. Failing tasks retry five times and then stop; click the button again to start over. Datastore statistics (`__Stat_Kind__`) refresh about daily.

The classifier is in `src/backend/common/queries/cached_query_orphans.py`. It never deletes a key it cannot parse or attribute to a known query class, and it matches classes on their full key format, because prefixes overlap (`event_{event_key}` also matches `event_awards_2024casj`).

## Flask Page Caching

Compute instance hours are one of the more expensive parts of App Engine, and rendering HTML pages is repetitive and CPU time consuming. We can cache the rendered page outputs to minimize that!

We use the [`flask-caching`](https://flask-caching.readthedocs.io/en/latest/) library to integrate with the `@cached_public` decorator used to annotate views that return public data we can cache.

On successful responses, we write the resulting HTML into the same App Engine bundled memcache described above, via `MemcacheFlaskResponseCache` (`src/backend/common/flask_cache.py`). If a pre-cached version of the page is present at the beginning of the request, we skip processing it and return the cached value.

> **Careful:** the cache key is the path plus query string — it has **no user component**. Anything user-specific rendered into a `@cached_public` page will be served to every other visitor. That includes CSRF tokens; see #10495 for a bug caused by exactly this.

## Cloudflare CDN Edge Caching

Finally, once we serve a request out of App Engine, it goes through [Cloudflare's CDN](https://support.cloudflare.com/hc/en-us/articles/200172516-Understanding-Cloudflare-s-CDN). The [CDN](https://en.wikipedia.org/wiki/Content_delivery_network) can cache pages at the "edge" of Cloudflare's network (physically closer to the user).

Cloudflare respects the standard HTTP caching headers. We use two:
 - [`Cache-Control`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control), which lets us set the expiry of each response
 - [`Etag`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag), which lets us version cached responses, which lets us skip sending content we know to be unchanged over the wire and instead return [`304 Not Modified`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/304)

 Additionally, most web browsers respect these cache headers themselves and will skip asking the server for data it's already cached locally, assuming it has not yet expired.
