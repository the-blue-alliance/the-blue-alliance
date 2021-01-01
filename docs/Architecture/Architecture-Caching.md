In order to keep costs down, TBA uses multiple [caching](https://en.wikipedia.org/wiki/Cache_(computing)) stragegies. In essence, we duplicate data in a faster or cheaper storage location in order to optimize for performance or costs.

There are a number of layers of caching. Here is an over of each, from lowest to highest level.

## NDB Caching

TBA uses the [`google-cloud-ndb`](https://googleapis.dev/python/python-ndb/latest/) library to interface with the datastore. This library has two caching mechanisms built in. [This page](https://cloud.google.com/appengine/docs/standard/python/ndb/cache) describes the caching behavior of the legacy python2.7 NDB library, which the new one emulates.

### Per-Request Context Cache

Each HTTP request has its own "context" which is visible to only that request. Within the context, the NDB library stores every entity it sees in memory. On reads, the context cache is checked first, and if present, a value is returned. The result of reads is also written back to the context cache, for the benefit of future reads. Additionally, data being written is also duplicated in the context cache.

### Global Redis Cache

The legacy NDB libray used legacy App Engine's hosted memcache as a layer after the context cache. Memcache is slower than the in-context cache, but still faster than reading from the datastore. The Cloud NDB library connects to a Redis instance running on [Google Cloud Memorystore](https://cloud.google.com/memorystore) and reads/writes to it with similar semantics to the context cache.

This cache is "write through" (which means the NDB library automatically updates data stored when it changes), and therefore does not have an expiration time by default (although we can configure it if we so choose). Redis also has a finite storage capacity and will evict data when the cache is full using a [least recently used](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)) algorithm.

The main differences is that the global cache is shared between requests, while the context cache is isolated to a single request.

## Application Level Query Caching

TBA's workload often involves making complex queries that span many datastore entires (for example, fetching the list of all matches at an event). The output of these queries is used by the webapp to render output pages and is also transformed into JSON objects for API representation.

The results of these queries is highly deterministic and repeatable, so it is a good candidate for caching. Plus, for large range queries, we can minimize round trips to the datastore by storing the entire response in a single object.

We have a special DB model named `CachedQueryResult` that stores the output of other DB queries. We can store both raw models, or JSON structured dictionaries for the API.

These objects do not have an expiration, so they need to manually cleared when the data within changes. This means we need to maintain a mechanism to do so within our application code. This logic is typically handled by the `Manipulator` classes, which contain the abstractions for doing DB writes.

## Flask Page Caching

Compute instance hours are one of the more expensive parts of App Engine, and rendering HTML pages is repetitive and CPU time consuming. We can cache the rendered page outputs to minimize that!

We use the [`flask-caching`](https://flask-caching.readthedocs.io/en/latest/) library to integrate with the `@cached_public` decorator used to annotate views that return public data we can cache.

On successful responses, we write the resulting HTML into Redis (again, running in [Google Cloud Memorystore](https://cloud.google.com/memorystore)). If a pre-cached version of the page is present in the cache at the beginning of the request, we skip processing it and instead return the value fetched from cache.

## Cloudflare CDN Edge Caching

Finally, once we serve a request out of App Engine, it goes through [Cloudflare's CDN](https://support.cloudflare.com/hc/en-us/articles/200172516-Understanding-Cloudflare-s-CDN). The [CDN](https://en.wikipedia.org/wiki/Content_delivery_network) can cache pages at the "edge" of Cloudflare's network (physically closer to the user).

Cloudflare respects the standard HTTP caching headers. We use two:
 - [`Cache-Control`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control), which lets us set the expiry of each response
 - [`Etag`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag), which lets us version cached responses, which lets us skip sending content we know to be unchanged over the wire and instead return [`304 Not Modified`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/304)

 Additionally, most web browsers respect these cache headers themselves and will skip asking the server for data it's already cached locally, assuming it has not yet expired.
