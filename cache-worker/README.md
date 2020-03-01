# cache-worker

A Cloudflare Worker for ensuring the TBA cache is being invalidated properly

## History

Sometime in February 2020, Cloudflare stopped respecting `cache-control` headers on some responses. Periodically, instead of responses being revalidated at the specified `max-age`, responses were staying cached for 2 hours (the default Cloudflare Edge Cache TTL).

## Purpose

This very thin Cloudflare Worker will validate that every response's `age` is less than it's `max-age`, as we expect. If a response's `age` is greater than it's `max-age`, the cached response is deleted from the cache, and a new response is fetched from the origin.

If the response is not cached, or if a response's `age` is less than it's `max-age`, we'll fallback to the default Cloudflare caching semantics.

A `X-TBA-Cache-Status` header is set on responses that the worker manually deletes the previously cached content for. For each response with this header, an event is logged in Google Analytics.
