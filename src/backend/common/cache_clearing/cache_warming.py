import logging
from typing import Any, Generator, List

from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.profiler import Span
from backend.common.queries.database_query import CachedDatabaseQuery


@ndb.tasklet
def _warm_query_async(query: CachedDatabaseQuery) -> Generator[Any, Any, None]:
    with Span("cache_warming.warm_query") as span:
        span.set_label("query_class", query.__class__.__name__)
        span.set_label("cache_key", query.cache_key)
        try:
            yield query.fetch_json_async(ApiMajorVersion.API_V3)
        except Exception as e:
            logging.warning(f"Failed to warm cache for query {query.cache_key}: {e}")


def warm_cache_queries(queries: List[CachedDatabaseQuery]) -> None:
    """
    Eagerly warms the query cache for the given queries by fetching pre-serialized JSON bytes.
    This populates CachedQueryResult in Datastore so subsequent user requests hit warm cache.
    """
    if not queries:
        return

    with Span("cache_warming.warm_cache_queries") as span:
        span.set_label("num_queries", str(len(queries)))
        logging.info(
            f"Warming query cache for {len(queries)} queries: {[q.cache_key for q in queries]}"
        )
        futures = [_warm_query_async(query) for query in queries]
        for future in futures:
            try:
                future.get_result()
            except Exception as e:
                logging.warning(f"Error while awaiting warm query future: {e}")
