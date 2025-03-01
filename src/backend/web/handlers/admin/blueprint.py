from flask import abort, Blueprint
from google.appengine.api import users as gae_login

from backend.common.environment import Environment
from backend.web.handlers.admin.api_auth import (
    api_auth_add,
    api_auth_delete,
    api_auth_delete_post,
    api_auth_edit,
    api_auth_edit_post,
    api_auth_manage,
)
from backend.web.handlers.admin.apistatus import apistatus_get, apistatus_post
from backend.web.handlers.admin.authkeys import authkeys_get, authkeys_post
from backend.web.handlers.admin.awards import (
    award_dashboard,
    award_delete_post,
    award_edit,
    award_edit_post,
)
from backend.web.handlers.admin.cache import (
    cached_query_delete,
    cached_query_detail,
    cached_query_info,
    cached_query_key_lookup_post,
    cached_query_list,
    cached_query_purge_version,
)
from backend.web.handlers.admin.districts import (
    district_create,
    district_delete,
    district_delete_post,
    district_details,
    district_edit,
    district_edit_post,
    district_list,
)
from backend.web.handlers.admin.event import (
    event_add_webcast_post,
    event_create,
    event_delete,
    event_delete_matches,
    event_detail,
    event_detail_post,
    event_edit,
    event_edit_post,
    event_list,
    event_remap_teams_post,
    event_remove_webcast_post,
    event_update_location_get,
    event_update_location_post,
)
from backend.web.handlers.admin.gameday import gameday_dashboard, gameday_dashboard_post
from backend.web.handlers.admin.landing import (
    landing_edit,
)
from backend.web.handlers.admin.match import (
    match_add,
    match_dashboard,
    match_delete,
    match_delete_post,
    match_detail,
    match_edit,
    match_edit_post,
    match_override_score_breakdown,
)
from backend.web.handlers.admin.media import (
    media_add,
    media_dashboard,
    media_delete_reference,
    media_make_preferred,
    media_remove_preferred,
)
from backend.web.handlers.admin.regional_champs_pool import regional_champs_pool_list
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
from backend.web.handlers.admin.team_media_mod import (
    team_media_mod_add,
    team_media_mod_add_post,
    team_media_mod_edit,
    team_media_mod_edit_post,
    team_media_mod_list,
)
from backend.web.handlers.admin.users import (
    user_detail,
    user_edit,
    user_edit_post,
    user_list,
    user_lookup,
    user_lookup_post,
    user_permissions_list,
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


@admin_routes.route("/")
def admin_home() -> str:
    template_values = {
        "memcache_stats": {
            "hits": 0,
            "misses": 0,
        },
        "databasequery_stats": {
            "hits": 0,
            "misses": 0,
        },
        "users": [],
        "suggestions_count": 0,
        "contbuild_enabled": False,
        "git_branch_name": "",
        "build_time": "",
        "build_number": "",
        "commit_hash": "",
        "commit_author": "",
        "commit_date": "",
        "commit_msg": "",
        "debug": Environment.is_dev(),
    }
    return render_template("admin/index.html", template_values)


@admin_routes.route("/tasks")
def task_launcher() -> str:
    return render_template("admin/tasks.html")


# More complex endpoints should be split out into their own files
admin_routes.add_url_rule("/api_auth/add", view_func=api_auth_add, methods=["GET"])
admin_routes.add_url_rule(
    "/api_auth/delete/<auth_id>", view_func=api_auth_delete, methods=["GET"]
)
admin_routes.add_url_rule(
    "/api_auth/delete/<auth_id>", view_func=api_auth_delete_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/api_auth/edit/<auth_id>", view_func=api_auth_edit, methods=["GET"]
)
admin_routes.add_url_rule(
    "/api_auth/edit/<auth_id>", view_func=api_auth_edit_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/api_auth/manage",
    view_func=api_auth_manage,
    defaults={"key_type": None},
    methods=["GET"],
)
admin_routes.add_url_rule(
    "/api_auth/manage/<regex('(read|write|admin)'):key_type>",
    view_func=api_auth_manage,
    methods=["GET"],
)
admin_routes.add_url_rule("/apistatus", view_func=apistatus_get, methods=["GET"])
admin_routes.add_url_rule("/apistatus", view_func=apistatus_post, methods=["POST"])
admin_routes.add_url_rule("/authkeys", view_func=authkeys_get, methods=["GET"])
admin_routes.add_url_rule("/authkeys", view_func=authkeys_post, methods=["POST"])

admin_routes.add_url_rule("/awards", view_func=award_dashboard)
admin_routes.add_url_rule(
    "/award/delete", methods=["POST"], view_func=award_delete_post
)
admin_routes.add_url_rule(
    "/award/edit/<award_key>", methods=["GET"], view_func=award_edit
)
admin_routes.add_url_rule(
    "/award/edit/<award_key>", methods=["POST"], view_func=award_edit_post
)
admin_routes.add_url_rule("/cache", view_func=cached_query_list)
admin_routes.add_url_rule(
    "/cache/<query_class_name>", methods=["GET"], view_func=cached_query_detail
)
admin_routes.add_url_rule(
    "/cache/<query_class_name>",
    methods=["POST"],
    view_func=cached_query_key_lookup_post,
)
admin_routes.add_url_rule(
    "/cache/<query_class_name>/<cache_key>", view_func=cached_query_info
)
admin_routes.add_url_rule(
    "/cache/<query_class_name>/<cache_key>/delete", view_func=cached_query_delete
)
admin_routes.add_url_rule(
    "/cache/<query_class_name>/purge/<db_version>/<int:query_version>",
    view_func=cached_query_purge_version,
)
admin_routes.add_url_rule(
    "/districts", view_func=district_list, defaults={"year": None}
)
admin_routes.add_url_rule("/districts/<int:year>", view_func=district_list)
admin_routes.add_url_rule("/district/<district_key>", view_func=district_details)
admin_routes.add_url_rule("/district/create", view_func=district_create)
admin_routes.add_url_rule(
    "/district/delete/<district_key>", methods=["GET"], view_func=district_delete
)
admin_routes.add_url_rule(
    "/district/delete/<district_key>", methods=["POST"], view_func=district_delete_post
)
admin_routes.add_url_rule(
    "/district/edit/",
    methods=["POST"],
    view_func=district_edit_post,
    defaults={"district_key": None},
)
admin_routes.add_url_rule(
    "/district/edit/<district_key>", methods=["POST"], view_func=district_edit_post
)
admin_routes.add_url_rule(
    "/district/edit/<district_key>", methods=["GET"], view_func=district_edit
)

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
    "/event/edit",
    view_func=event_edit_post,
    defaults={"event_key": None},
    methods=["POST"],
)
admin_routes.add_url_rule("/event/<event_key>", view_func=event_detail, methods=["GET"])
admin_routes.add_url_rule(
    "/event/<event_key>", view_func=event_detail_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/event/add_webcast/<event_key>", view_func=event_add_webcast_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/event/remap_teams/<event_key>", view_func=event_remap_teams_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/event/remove_webcast/<event_key>",
    view_func=event_remove_webcast_post,
    methods=["POST"],
)
admin_routes.add_url_rule(
    "/event/delete_matches/<event_key>/<comp_level>/<to_delete>",
    view_func=event_delete_matches,
    methods=["GET"],
)
admin_routes.add_url_rule(
    "/event/update_location/<event_key>",
    view_func=event_update_location_get,
    methods=["GET"],
)
admin_routes.add_url_rule(
    "/event/update_location/<event_key>",
    view_func=event_update_location_post,
    methods=["POST"],
)
admin_routes.add_url_rule("/events", view_func=event_list, defaults={"year": None})
admin_routes.add_url_rule("/events/<int:year>", view_func=event_list)
admin_routes.add_url_rule("/matches", view_func=match_dashboard, methods=["GET"])
admin_routes.add_url_rule("/match/add", view_func=match_add, methods=["POST"])
admin_routes.add_url_rule(
    "/match/override_breakdown",
    view_func=match_override_score_breakdown,
    methods=["POST"],
)
admin_routes.add_url_rule("/match/<match_key>", view_func=match_detail, methods=["GET"])
admin_routes.add_url_rule(
    "/match/edit/<match_key>", view_func=match_edit, methods=["GET"]
)
admin_routes.add_url_rule(
    "/match/edit/<match_key>", view_func=match_edit_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/match/delete/<match_key>", view_func=match_delete, methods=["GET"]
)
admin_routes.add_url_rule(
    "/match/delete/<match_key>", view_func=match_delete_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/regional_champs_pool",
    view_func=regional_champs_pool_list,
    defaults={"year": None},
)
admin_routes.add_url_rule(
    "/regional_champs_pool/<int:year>", view_func=regional_champs_pool_list
)
admin_routes.add_url_rule("/sitevars", view_func=sitevars_list)
admin_routes.add_url_rule("/sitevar/create", view_func=sitevar_create, methods=["GET"])
admin_routes.add_url_rule(
    "/sitevar/edit/<sitevar_key>", view_func=sitevar_edit, methods=["GET"]
)
admin_routes.add_url_rule(
    "/sitevar/edit", view_func=sitevar_edit_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/sitevar/edit/<sitevar_key>", view_func=sitevar_edit_post, methods=["POST"]
)
admin_routes.add_url_rule("/gameday", methods=["GET"], view_func=gameday_dashboard)
admin_routes.add_url_rule(
    "/gameday", methods=["POST"], view_func=gameday_dashboard_post
)
admin_routes.add_url_rule(
    "/main_landing", view_func=landing_edit, methods=["GET", "POST"]
)
admin_routes.add_url_rule("/teams", view_func=team_list)
admin_routes.add_url_rule("/teams/<int:page_num>", view_func=team_list)
admin_routes.add_url_rule("/team/<int:team_number>", view_func=team_detail)
admin_routes.add_url_rule(
    "/team/website", view_func=team_website_update, methods=["POST"]
)

admin_routes.add_url_rule("/media", view_func=media_dashboard)
admin_routes.add_url_rule("/media/add_media", methods=["POST"], view_func=media_add)
admin_routes.add_url_rule(
    "/media/delete_reference/<media_key_name>",
    methods=["POST"],
    view_func=media_delete_reference,
)
admin_routes.add_url_rule(
    "/media/make_preferred/<media_key_name>",
    methods=["POST"],
    view_func=media_make_preferred,
)
admin_routes.add_url_rule(
    "/media/remove_preferred/<media_key_name>",
    methods=["POST"],
    view_func=media_remove_preferred,
)
admin_routes.add_url_rule("/media/modcodes/list", view_func=team_media_mod_list)
admin_routes.add_url_rule(
    "/media/modcodes/list/<int:year>", view_func=team_media_mod_list
)
admin_routes.add_url_rule(
    "/media/modcodes/list/<int:year>/<int:page_num>", view_func=team_media_mod_list
)
admin_routes.add_url_rule("/media/modcodes/add", view_func=team_media_mod_add)
admin_routes.add_url_rule(
    "/media/modcodes/add", view_func=team_media_mod_add_post, methods=["POST"]
)
admin_routes.add_url_rule(
    "/media/modcodes/edit/<int:team_number>/<int:year>",
    view_func=team_media_mod_edit,
)
admin_routes.add_url_rule(
    "/media/modcodes/edit/<int:team_number>/<int:year>",
    view_func=team_media_mod_edit_post,
    methods=["POST"],
)
admin_routes.add_url_rule(
    "/team/set_robot_name", view_func=team_robot_name_update, methods=["POST"]
)
admin_routes.add_url_rule("/user/<user_id>", view_func=user_detail)
admin_routes.add_url_rule("/user/edit/<user_id>", methods=["GET"], view_func=user_edit)
admin_routes.add_url_rule(
    "/user/edit/<user_id>", methods=["POST"], view_func=user_edit_post
)
admin_routes.add_url_rule("/user/lookup", methods=["GET"], view_func=user_lookup)
admin_routes.add_url_rule("/user/lookup", methods=["POST"], view_func=user_lookup_post)
admin_routes.add_url_rule("/users", view_func=user_list, defaults={"page_num": 0})
admin_routes.add_url_rule("/users/<int:page_num>", view_func=user_list)
admin_routes.add_url_rule("/users/permissions", view_func=user_permissions_list)
