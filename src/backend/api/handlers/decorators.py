import json
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from flask import g, jsonify, make_response, request, Response

from backend.api.client_api_types import VoidRequest
from backend.api.handlers.helpers.etag_helper import (
    get_incoming_etags,
    get_request_path,
    is_etag_valid,
    normalize_etag,
    save_etag_dependencies,
)
from backend.common.cache.instance_cache import InstanceCache
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_code_exceptions import EventCodeExceptions
from backend.common.consts.fms_report_type import FMSReportType
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.environment import Environment
from backend.common.logging import set_logging_context
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.profiler import Span
from backend.common.queries.database_query import track_accessed_query_cache_keys


@dataclass(frozen=True)
class CachedAuth:
    owner_id: Optional[str]
    description: Optional[str]


AUTH_KEY_CACHE_TTL: float = 600.0  # 10 minutes
AUTH_KEY_CACHE_MAX_SIZE: int = 1000
auth_key_cache: InstanceCache[str, CachedAuth] = InstanceCache(
    ttl_seconds=AUTH_KEY_CACHE_TTL, max_size=AUTH_KEY_CACHE_MAX_SIZE
)


def api_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        with Span("api_authenticated") as span:
            auth_key = request.headers.get(
                "X-TBA-Auth-Key", request.args.get("X-TBA-Auth-Key")
            )

            auth_owner_id = None

            if auth_key:
                cached_auth = auth_key_cache.get(auth_key)
                if cached_auth is None:
                    auth = ApiAuthAccess.get_by_id(auth_key)
                    if not auth:
                        return (
                            {
                                "Error": "X-TBA-Auth-Key is invalid. Please get an access key at http://www.thebluealliance.com/account."
                            },
                            401,
                        )
                    cached_auth = CachedAuth(
                        owner_id=auth.owner.id() if auth.owner else None,
                        description=auth.description,
                    )
                    auth_key_cache.set(auth_key, cached_auth)
                else:
                    span.set_label("auth_cached", "true")

                auth_owner_id = cached_auth.owner_id
                # Set for our GA event tracking in `track_call_after_response`
                g.auth_description = cached_auth.description
                # Add API key to logging context for searchability in logs
                set_logging_context("api_auth_key", auth_key)
                # Add to trace span for visibility in Cloud Trace
                span.set_label("api_auth_key", auth_key)
                span.set_label("auth_owner_id", str(auth_owner_id))
                # Log API key usage for visibility in GCP Console
                logging.info(
                    f"API request authenticated with key: {auth_key[:16]}... (owner: {auth_owner_id})"
                )
            else:
                from backend.common.auth import current_user

                user = current_user()
                if user:
                    auth_owner_id = user.account_key.id()
                else:
                    return (
                        {
                            "Error": "X-TBA-Auth-Key is a required header or URL param. Please get an access key at http://www.thebluealliance.com/account."
                        },
                        401,
                    )

            # Set for our GA event tracking in `track_call_after_response`
            g.auth_owner_id = auth_owner_id

        return func(*args, **kwargs)

    return decorated_function


def require_write_auth(auth_types: set[AuthType] | None, file_param: str | None = None):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            with Span("require_write_auth"):
                event_key = kwargs["event_key"]
                fms_report_type = kwargs.get("report_type")
                # Check if report_type is a valid FMS report type
                if fms_report_type:
                    try:
                        FMSReportType(fms_report_type)
                    except ValueError:
                        fms_report_type = None

                # This will abort the request on failure
                from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper

                TrustedApiAuthHelper.do_trusted_api_auth(
                    event_key, fms_report_type, auth_types, file_param
                )
            return func(*args, **kwargs)

        return decorated_function

    return decorator


def require_moderation_permission(permissions: set[AccountPermission]):
    """
    Authenticate the request via a Firebase ID token in the Authorization
    header (the same mechanism as the client API) and require the resolved
    account to hold any of the given AccountPermissions. Admins always pass.
    The resolved User is stored on flask.g.moderation_user.
    """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            with Span("require_moderation_permission"):
                from backend.api.client_api_auth_helper import ClientApiAuthHelper

                user = ClientApiAuthHelper.get_current_user()
                if user is None:
                    return make_response(
                        jsonify(
                            {
                                "Error": "Authorization required. Pass a Firebase ID token "
                                "as 'Authorization: Bearer <token>'."
                            }
                        ),
                        401,
                    )
                # Accounts are linked to tokens by email claim, so an
                # unverified email must never confer the linked account's
                # permissions
                if not user.email_verified:
                    return make_response(
                        jsonify(
                            {
                                "Error": "Moderation requires a verified email on your "
                                "sign-in provider."
                            }
                        ),
                        403,
                    )
                if not user.is_admin and not permissions.intersection(
                    user.permissions or []
                ):
                    return make_response(
                        jsonify(
                            {
                                "Error": "You do not have permission to moderate suggestions. "
                                "If this is incorrect, please contact TBA admins."
                            }
                        ),
                        403,
                    )
                g.moderation_user = user
            return func(*args, **kwargs)

        return decorated_function

    return decorator


T = TypeVar("T")
R = TypeVar("R")


def client_api_method(
    req_type: Type[T], resp_type: Type[R]
) -> Callable[[Callable[[T], R]], Callable[..., Response]]:
    """
    This is a decorator to apply JSON request/response models
    to the API methods
    """

    def decorator(func: Callable[[T], R]) -> Callable[..., Response]:
        @wraps(func)
        def decorated_function(*args, **kwargs) -> Response:
            data = request.get_data()
            if data:
                req = json.loads(data)
            else:
                req = VoidRequest()

            resp = func(req)
            return jsonify(resp)

        return decorated_function

    return decorator


KEY_EXISTS_CACHE_TTL: float = 600.0  # 10 minutes
KEY_EXISTS_CACHE_MAX_SIZE: int = 5000
key_exists_cache: InstanceCache[tuple[str, str], bool] = InstanceCache(
    ttl_seconds=KEY_EXISTS_CACHE_TTL, max_size=KEY_EXISTS_CACHE_MAX_SIZE
)

KEY_DOES_NOT_EXIST_CACHE_TTL: float = 60.0  # 1 minute (aligned with 61s 404 cache)
KEY_DOES_NOT_EXIST_CACHE_MAX_SIZE: int = 2000
key_does_not_exist_cache: InstanceCache[tuple[str, str], bool] = InstanceCache(
    ttl_seconds=KEY_DOES_NOT_EXIST_CACHE_TTL, max_size=KEY_DOES_NOT_EXIST_CACHE_MAX_SIZE
)


@dataclass(frozen=True)
class _KeyValidator:
    param_name: str
    key_type: str
    entity_name: str
    validate_format: Callable[[str], bool]
    fetch_async: Callable[[str], Any]
    resolve_key: Optional[Callable[[str], str]] = None


_KEY_VALIDATORS: tuple[_KeyValidator, ...] = (
    _KeyValidator(
        param_name="team_key",
        key_type="team",
        entity_name="Team",
        validate_format=Team.validate_key_name,
        fetch_async=Team.get_by_id_async,
    ),
    _KeyValidator(
        param_name="event_key",
        key_type="event",
        entity_name="Event",
        validate_format=Event.validate_key_name,
        fetch_async=Event.get_by_id_async,
        resolve_key=EventCodeExceptions.resolve,
    ),
    _KeyValidator(
        param_name="match_key",
        key_type="match",
        entity_name="Match",
        validate_format=Match.validate_key_name,
        fetch_async=Match.get_by_id_async,
    ),
    _KeyValidator(
        param_name="district_key",
        key_type="district",
        entity_name="District",
        validate_format=District.validate_key_name,
        fetch_async=RenamedDistricts.district_exists_async,
    ),
)


def validate_keys(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        with Span("validate_keys"):
            # 1. Format validation
            for validator in _KEY_VALIDATORS:
                key = kwargs.get(validator.param_name)
                if key and not validator.validate_format(key):
                    return {
                        "Error": f"{key} is not a valid {validator.key_type} key"
                    }, 404

            # 2. Fast negative cache check
            for validator in _KEY_VALIDATORS:
                key = kwargs.get(validator.param_name)
                if key and (validator.entity_name, key) in key_does_not_exist_cache:
                    return {
                        "Error": f"{validator.key_type} key: {key} does not exist"
                    }, 404

            # 3. Check key existence for keys not already in key_exists_cache
            pending_checks: list[tuple[_KeyValidator, str, Optional[str], Any]] = []
            for validator in _KEY_VALIDATORS:
                key = kwargs.get(validator.param_name)
                if not key or (validator.entity_name, key) in key_exists_cache:
                    continue

                lookup_key = (
                    validator.resolve_key(key) if validator.resolve_key else key
                )
                if lookup_key != key:
                    if (validator.entity_name, lookup_key) in key_exists_cache:
                        key_exists_cache.set((validator.entity_name, key), True)
                        continue
                    if (validator.entity_name, lookup_key) in key_does_not_exist_cache:
                        key_does_not_exist_cache.set((validator.entity_name, key), True)
                        return {
                            "Error": f"{validator.key_type} key: {key} does not exist"
                        }, 404

                future = validator.fetch_async(lookup_key)
                pending_checks.append(
                    (validator, key, lookup_key if lookup_key != key else None, future)
                )

            # 4. Resolve futures and populate positive / negative caches
            for validator, key, resolved_key, future in pending_checks:
                with Span(f"validate_keys.resolve:{validator.entity_name}") as span:
                    span.set_label("lookup_key", key)
                    entity_result = future.get_result()
                    span.set_label("exists", str(bool(entity_result)))
                    if not entity_result:
                        key_does_not_exist_cache.set((validator.entity_name, key), True)
                        return {
                            "Error": f"{validator.key_type} key: {key} does not exist"
                        }, 404

                    key_exists_cache.set((validator.entity_name, key), True)
                    if resolved_key:
                        key_exists_cache.set(
                            (validator.entity_name, resolved_key), True
                        )

        return func(*args, **kwargs)

    return decorated_function


ETAG_304_CACHE_TTL: float = 15.0  # 15 seconds
ETAG_304_CACHE_MAX_SIZE: int = 2000
etag_304_cache: InstanceCache[tuple[str, str], bool] = InstanceCache(
    ttl_seconds=ETAG_304_CACHE_TTL, max_size=ETAG_304_CACHE_MAX_SIZE
)


def _make_304_response(etag: str) -> Response:
    response = Response(status=304)
    response.headers["ETag"] = f'"{etag}"'
    if Environment.cache_control_header_enabled():
        response.headers["Cache-Control"] = "public, max-age=61, s-maxage=61"
    return response


def validate_etag(func: Callable) -> Callable:
    """
    Decorator for APIv3 endpoints to short-circuit 304 responses when query dependencies haven't changed.
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        with Span("validate_etag") as span:
            if_none_match = request.headers.get("If-None-Match")
            if if_none_match:
                try:
                    request_path = get_request_path()
                    incoming_etags = get_incoming_etags()
                    for etag in incoming_etags:
                        if not etag:
                            continue

                        hit_source: Optional[str] = None
                        if etag_304_cache.get((request_path, etag)):
                            hit_source = "memory"
                        elif is_etag_valid(etag):
                            etag_304_cache.set((request_path, etag), True)
                            hit_source = "memcache"

                        if hit_source:
                            span.set_label("etag_cache_hit", hit_source)
                            return _make_304_response(etag)
                except Exception as e:
                    logging.warning(f"Error during validate_etag fast-path: {e}")

        with track_accessed_query_cache_keys() as accessed_keys:
            resp = make_response(func(*args, **kwargs))

            if resp.status_code == 200:
                try:
                    if not resp.headers.get("ETag"):
                        with Span("etag.compute_md5") as span:
                            resp.add_etag()
                            data = resp.get_data()
                            if data:
                                span.set_label("response_size_bytes", str(len(data)))
                    etag_header = resp.headers.get("ETag")
                    if etag_header and accessed_keys:
                        normalized = normalize_etag(etag_header)
                        if normalized:
                            with Span("etag.save_dependencies") as span:
                                span.set_label(
                                    "num_query_keys", str(len(accessed_keys))
                                )
                                save_etag_dependencies(normalized, accessed_keys)
                except Exception as e:
                    logging.warning(f"Error saving validate_etag dependencies: {e}")

            return resp

    return decorated_function
