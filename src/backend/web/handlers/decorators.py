from functools import wraps
from typing import Callable

from flask import abort, redirect, request, Response, url_for

from backend.common.consts.account_permission import AccountPermission
from backend.web.auth import current_user


def require_login_only(f: Callable) -> Response:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def require_login(f: Callable):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        if not user.is_registered:
            return redirect(url_for("account.register", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def enforce_login(f: Callable):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f: Callable) -> Response:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("account.login", next=request.url))
        if not user.is_admin:
            return abort(401)
        return f(*args, **kwargs)

    return decorated_function


def require_permission(permission: AccountPermission):
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("account.login", next=request.url))
            if permission not in user.permissions:
                return abort(401)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
