from functools import wraps
from typing import Any, Callable, cast, Dict, List, Optional, Set, TypeVar, Union

from flask import abort, make_response, redirect, request, url_for
from flask.typing import ResponseValue
from google.appengine.ext import ndb

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.models.audit_log_entry import AuditLogEntry

TResponseFunc = TypeVar("TResponseFunc", bound=Callable[..., ResponseValue])


def require_login_only(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def require_login(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        if not user.is_registered:
            return redirect(url_for("account.register", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def enforce_login(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        if not user.is_admin:
            return abort(401)
        return f(*args, **kwargs)

    return decorated_function


def require_permission(
    permission: AccountPermission,
) -> Callable[..., Callable[..., ResponseValue]]:
    def decorator(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("account.login", next=request.url))
            if not user.is_admin and permission not in user.permissions:
                return abort(401)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_any_permission(
    permissions: Set[AccountPermission],
) -> Callable[..., Callable[..., ResponseValue]]:
    def decorator(f: Callable[..., ResponseValue]) -> Callable[..., ResponseValue]:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("account.login", next=request.url))
            if not user.is_admin and not permissions.intersection(
                user.permissions or {}
            ):
                return abort(401)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def _serialize_url_args(url_args: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if url_args is None:
        return {}
    return {str(key): str(value) for key, value in url_args.items()}


def _serialize_form_params(form: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {key: values for key, values in form.items() if key != "csrf_token"}


def audit_post_mutation(
    f: Optional[TResponseFunc] = None,
    *,
    target_key_getter: Optional[Callable[..., Optional[ndb.Key]]] = None,
) -> Union[TResponseFunc, Callable[[TResponseFunc], TResponseFunc]]:
    def decorator(func: TResponseFunc) -> TResponseFunc:
        @wraps(func)
        def decorated_function(*args, **kwargs):
            response = func(*args, **kwargs)
            response_obj = make_response(response)

            if response_obj.status_code < 400 and request.endpoint is not None:
                user = current_user()
                target_key = None
                if target_key_getter is not None:
                    target_key = target_key_getter(*args, **kwargs)

                AuditLogEntry(
                    account=user.account_key if user else None,
                    endpoint=request.endpoint,
                    target_key=target_key,
                    url_args=_serialize_url_args(request.view_args),
                    form_params=_serialize_form_params(
                        request.form.to_dict(flat=False)
                    ),
                ).put()

            return response

        return cast(TResponseFunc, decorated_function)

    if f is not None:
        return decorator(f)

    return decorator
