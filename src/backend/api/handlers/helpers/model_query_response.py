from typing import Any, Callable, Optional

from flask import abort

from backend.api.handlers.helpers.model_properties import ModelType
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
from backend.common.consts.api_version import ApiMajorVersion
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
        data = filter_func(data, model_type)
    return profiled_jsonify(data)
