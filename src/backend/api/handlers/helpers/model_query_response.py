from typing import Any, Callable, Iterable, Optional, Sequence

from flask import abort

from backend.api.handlers.helpers.model_properties import ModelType
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.profiler import Span
from backend.common.queries.database_query import CachedDatabaseQuery


def model_query_response(
    query: CachedDatabaseQuery,
    model_type: Optional[ModelType] = None,
    filter_func: Optional[Callable] = None,
    abort_404_if_none: bool = True,
) -> TypedFlaskResponse[Any]:
    """
    Handles a query for a single model entity.
    If model_type is None, fetches pre-serialized JSON bytes directly.
    If model_type is specified, fetches the dict, filters properties, and serializes.
    """
    if model_type is None:
        raw_json = query.fetch_json(ApiMajorVersion.API_V3)
        if raw_json is None and abort_404_if_none:
            abort(404)
        return profiled_jsonify(raw_json)

    data = query.fetch_dict(ApiMajorVersion.API_V3)
    if data is None:
        if abort_404_if_none:
            abort(404)
        return profiled_jsonify(None)
    if filter_func is not None:
        with Span("model_query_response.filter_properties") as span:
            span.set_label("model_type", str(model_type))
            span.set_label("item_count", "1")
            data = filter_func([data], model_type)[0]
    return profiled_jsonify(data)


def models_query_response(
    query: CachedDatabaseQuery,
    model_type: Optional[ModelType] = None,
    filter_func: Optional[Callable] = None,
) -> TypedFlaskResponse[Any]:
    """
    Handles a query for a collection of model entities.
    If model_type is None, fetches pre-serialized JSON bytes directly.
    If model_type is specified, fetches the dicts, filters properties, and serializes.
    """
    if model_type is None:
        raw_json = query.fetch_json(ApiMajorVersion.API_V3)
        return profiled_jsonify(raw_json)

    data = query.fetch_dict(ApiMajorVersion.API_V3)
    if filter_func is not None and data is not None:
        with Span("model_query_response.filter_properties") as span:
            span.set_label("model_type", str(model_type))
            span.set_label("item_count", str(len(data)))
            data = filter_func(data, model_type)
    return profiled_jsonify(data)


def combine_json_arrays(chunks: Iterable[Optional[bytes]]) -> bytes:
    """
    Combines multiple pre-serialized JSON array byte chunks into a single JSON array byte payload.
    """
    with Span("combine_json_arrays") as span:
        valid_slices: list[bytes] = []
        num_chunks = 0
        for raw_chunk in chunks:
            num_chunks += 1
            if raw_chunk:
                stripped = raw_chunk.strip()
                if (
                    len(stripped) >= 2
                    and stripped.startswith(b"[")
                    and stripped.endswith(b"]")
                ):
                    inner = stripped[1:-1].strip()
                    if inner:
                        valid_slices.append(inner)
        payload = b"[" + b",".join(valid_slices) + b"]"
        span.set_label("num_chunks", str(num_chunks))
        span.set_label("valid_slices_count", str(len(valid_slices)))
        span.set_label("payload_size_bytes", str(len(payload)))
        return payload


def multi_models_query_response(
    queries: Sequence[CachedDatabaseQuery],
    model_type: Optional[ModelType] = None,
    filter_func: Optional[Callable] = None,
) -> TypedFlaskResponse[Any]:
    """
    Handles multiple queries for collections of model entities.
    If model_type is None, fetches pre-serialized JSON bytes asynchronously and combines at the byte level.
    If model_type is specified, fetches dicts asynchronously, combines them, filters properties, and serializes.
    """
    if model_type is None:
        futures = [q.fetch_json_async(ApiMajorVersion.API_V3) for q in queries]
        payload = combine_json_arrays(f.get_result() for f in futures)
        return profiled_jsonify(payload)

    futures = [q.fetch_dict_async(ApiMajorVersion.API_V3) for q in queries]
    items = []
    for f in futures:
        partial = f.get_result()
        if partial:
            items += partial

    if filter_func is not None and items is not None:
        with Span("model_query_response.filter_properties") as span:
            span.set_label("model_type", str(model_type))
            span.set_label("item_count", str(len(items)))
            items = filter_func(items, model_type)
    return profiled_jsonify(items)
