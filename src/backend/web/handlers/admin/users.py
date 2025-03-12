from flask import abort, redirect, request, url_for
from werkzeug import Response

from backend.common.consts.account_permission import AccountPermission, PERMISSIONS
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.web.profiled_render import render_template


USER_PAGE_SIZE = 1000


def user_list(page_num: int) -> str:
    num_users = Account.query().count()
    max_page = (num_users // USER_PAGE_SIZE) + 1

    if page_num <= max_page:
        offset = USER_PAGE_SIZE * page_num
    else:
        page_num = 0
        offset = 0
    users = Account.query().order(Account.created).fetch(USER_PAGE_SIZE, offset=offset)

    template_values = {
        "num_users": num_users,
        "users": users,
        "page_num": page_num,
        "page_labels": [p + 1 for p in range(max_page + 1)],
    }
    return render_template("admin/user_list.html", template_values)


def user_detail(user_id: str) -> str:
    user = Account.get_by_id(user_id)
    if user is None:
        abort(404)

    api_keys = ApiAuthAccess.query(ApiAuthAccess.owner == user.key).fetch()

    template_values = {
        "user": user,
        "api_keys": api_keys,
        "permissions": PERMISSIONS,
    }
    return render_template("admin/user_details.html", template_values)


def user_edit(user_id: str) -> str:
    user = Account.get_by_id(user_id)
    if user is None:
        abort(404)

    template_values = {
        "user": user,
        "permissions": PERMISSIONS,
    }
    return render_template("admin/user_edit.html", template_values)


def user_edit_post(user_id: str) -> Response:
    user = Account.get_by_id(user_id)
    if user is None:
        abort(404)

    user.display_name = request.form.get("display_name", "")
    user.shadow_banned = True if request.form.get("shadow_banned") else False
    user.permissions = []
    for permission in iter(AccountPermission):
        permchek = request.form.get(f"perm-{permission.value}")
        if permchek:
            user.permissions.append(permission)
    user.put()

    return redirect(url_for("admin.user_detail", user_id=user_id))


def user_lookup() -> str:
    return render_template("admin/user_lookup.html")


def user_lookup_post() -> Response:
    user_email = request.form.get("email")
    if not user_email:
        abort(404)

    users = Account.query(Account.email == user_email).fetch()
    if not users:
        abort(404)

    user = users[0]
    return redirect(url_for("admin.user_detail", user_id=user.key.id()))


def user_permissions_list() -> str:
    users = Account.query(Account.permissions != None).fetch()  # noqa: E711
    template_values = {
        "users": users,
        "permissions": PERMISSIONS,
    }
    return render_template("admin/user_permissions_list.html", template_values)
