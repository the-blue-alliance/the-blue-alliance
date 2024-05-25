from flask import abort, Blueprint
from google.appengine.api import users as gae_login

from backend.tasks_io.handlers.admin.tasks import admin_clear_eventteams


"""
This is a special interface available to TBA admins to manage data
"""

admin_routes = Blueprint("admin", __name__, url_prefix="/tasks/admin")


@admin_routes.before_request
def require_gae_admin() -> None:
    """
    Ensure that only admins can access this blueprint
    """
    if not gae_login.is_current_user_admin():
        abort(401)


@admin_routes.route("/do/nothing")
def test_admin_task_view() -> str:
    return "success"


admin_routes.add_url_rule(
    "/do/clear_eventteams/<event_key>", view_func=admin_clear_eventteams
)
