from flask import abort, Blueprint
from google.appengine.api import users as gae_login

from backend.web.handlers.admin.authkeys import authkeys_get, authkeys_post
from backend.web.handlers.admin.event import (
    event_create,
    event_delete,
    event_detail,
    event_edit,
    event_edit_post,
    event_list,
)
from backend.web.handlers.admin.sitevars import (
    sitevar_create,
    sitevar_edit,
    sitevar_edit_post,
    sitevars_list,
)
from backend.web.handlers.admin.team import (
    team_detail,
    team_list,
    team_robot_name_update,
    team_website_update,
)
from backend.web.profiled_render import render_template


"""
This is a special interface available to TBA admins to manage data
"""

admin_routes = Blueprint("admin", __name__, url_prefix="/admin")


@admin_routes.before_request
def require_gae_admin() -> None:
    """
    Ensure that only admins can access this blueprint
    """
    if not gae_login.is_current_user_admin():
        abort(401)


@admin_routes.route("/tasks")
def task_launcher() -> str:
    return render_template("admin/tasks.html")


# More complex endpoints should be split out into their own files
admin_routes.add_url_rule("/authkeys", view_func=authkeys_get, methods=["GET"])
admin_routes.add_url_rule("/authkeys", view_func=authkeys_post, methods=["POST"])
admin_routes.add_url_rule("/event/create", view_func=event_create, methods=["GET"])
admin_routes.add_url_rule(
    "/event/<event_key>/delete", view_func=event_delete, methods=["GET", "POST"]
)
admin_routes.add_url_rule(
    "/event/<event_key>/edit", view_func=event_edit, methods=["GET"]
)
admin_routes.add_url_rule(
    "/event/<event_key>/edit", view_func=event_edit_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/event/edit", view_func=event_edit_post, defaults={"event_key": None}, methods=["POST"],
)
admin_routes.add_url_rule("/event/<event_key>", view_func=event_detail)
admin_routes.add_url_rule("/events", view_func=event_list, defaults={"year": None})
admin_routes.add_url_rule("/events/<int:year>", view_func=event_list)
admin_routes.add_url_rule("/sitevars", view_func=sitevars_list)
admin_routes.add_url_rule("/sitevar/create", view_func=sitevar_create, methods=["GET"])
admin_routes.add_url_rule(
    "/sitevar/edit/<sitevar_key>", view_func=sitevar_edit, methods=["GET"]
)
admin_routes.add_url_rule(
    "/sitevar/edit/<sitevar_key>", view_func=sitevar_edit_post, methods=["POST"]
)
admin_routes.add_url_rule("/teams", view_func=team_list)
admin_routes.add_url_rule("/teams/<int:page_num>", view_func=team_list)
admin_routes.add_url_rule("/team/<int:team_number>", view_func=team_detail)
admin_routes.add_url_rule(
    "/team/website", view_func=team_website_update, methods=["POST"]
)
admin_routes.add_url_rule(
    "/team/set_robot_name", view_func=team_robot_name_update, methods=["POST"]
)
