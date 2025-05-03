import datetime

from flask import (
    abort,
    Blueprint,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.auth import (
    create_session_cookie,
    current_user,
    delete_user,
    revoke_session_cookie,
)
from backend.common.consts.auth_type import (
    WRITE_TYPE_NAMES as AUTH_TYPE_WRITE_TYPE_NAMES,
)
from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import (
    ENABLED_EVENT_NOTIFICATIONS,
    ENABLED_TEAM_NOTIFICATIONS,
    RENDER_NAMES as NOTIFICATION_RENDER_NAMES,
)
from backend.common.environment import Environment
from backend.common.helpers.account_deletion import AccountDeletionHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.mytba_helper import MyTBAHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.favorite import Favorite
from backend.common.models.keys import EventKey, TeamNumber
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.queries.event_query import TeamEventsQuery
from backend.common.sitevars.notifications_enable import NotificationsEnable
from backend.web.decorators import enforce_login, require_login, require_login_only
from backend.web.redirect import is_safe_url, safe_next_redirect

blueprint = Blueprint("account", __name__, url_prefix="/account")


@blueprint.route("")
@require_login
def overview() -> str:
    template_values = {
        "status": session.pop("account_status", None),
        "webhook_verification_success": request.args.get(
            "webhook_verification_success"
        ),
        "ping_sent": session.pop("ping_sent", None),
        "ping_enabled": NotificationsEnable.notifications_enabled(),
        "auth_write_type_names": AUTH_TYPE_WRITE_TYPE_NAMES,
    }
    return render_template("account_overview.html", **template_values)


@blueprint.route("/register", methods=["GET", "POST"])
@require_login_only
def register() -> Response:
    response = safe_next_redirect(url_for("account.overview"))

    user = none_throws(current_user())
    # Redirects if already registered
    if user.is_registered:
        return response

    if request.method == "POST":
        error_response = redirect("/")

        account_id = request.form.get("account_id")
        if not account_id or not account_id == user.uid:
            return error_response

        display_name = request.form.get("display_name")
        if not display_name:
            return error_response

        user.register(display_name)
        return response
    else:
        next = request.args.get("next")
        # Make sure `next` is safe - otherwise drop it
        next = next if next and is_safe_url(next) else None
        return make_response(render_template("account_register.html", next=next))


@blueprint.route("/edit", methods=["GET", "POST"])
@require_login
def edit() -> Response:
    if request.method == "POST":
        error_response = redirect(url_for("account.edit"))

        user = none_throws(current_user())
        account_id = request.form.get("account_id")
        if not account_id or not account_id == user.uid:
            session["account_edit_status"] = "account_edit_failure"
            return error_response

        display_name = request.form.get("display_name")
        if not display_name:
            session["account_edit_status"] = "account_edit_failure_name"
            return error_response

        user.update_display_name(display_name)

        _set_account_status("account_edit_success")
        return redirect(url_for("account.overview"))

    return make_response(
        render_template(
            "account_edit.html", status=session.pop("account_edit_status", None)
        )
    )


@blueprint.route("/delete", methods=["GET", "POST"])
@require_login
def delete() -> Response:
    if request.method == "POST":
        user = none_throws(current_user())

        # delete data in the TBA db for this user
        AccountDeletionHelper.delete_account(none_throws(user.account_key))

        # log out the current session
        revoke_session_cookie()

        # delete the user in firebase
        delete_user(str(user.uid))
        return redirect(url_for("index"))
    else:
        return make_response(render_template("account_delete.html"))


@blueprint.route("/login", methods=["GET", "POST"])
def login() -> Response:
    if request.method == "POST":
        id_token = request.form.get("id_token")
        if not id_token:
            abort(400)

        expires_in = datetime.timedelta(days=5)

        response = jsonify({"status": "success"})
        create_session_cookie(id_token, expires_in)
        return response
    else:
        if current_user():
            return redirect(url_for("account.overview"))

        auth_emulator_host = Environment.auth_emulator_host()
        return make_response(
            render_template(
                "account_login_required.html",
                next=next,
                auth_emulator_host=auth_emulator_host,
            )
        )


@blueprint.route("/logout")
@require_login_only
def logout() -> Response:
    revoke_session_cookie()
    return safe_next_redirect("/")


@blueprint.route("/api/read_key_add", methods=["POST"])
@enforce_login
def read_key_add() -> Response:
    response = redirect(url_for("account.overview"))

    description = request.form.get("description")
    if not description:
        _set_account_status("read_key_add_no_description")
        return response

    user = none_throws(current_user())
    try:
        user.add_api_read_key(description)
    except Exception:
        _set_account_status("read_key_add_failure")
        return response

    _set_account_status("read_key_add_success")
    return response


@blueprint.route("/api/read_key_delete", methods=["POST"])
@enforce_login
def read_key_delete() -> Response:
    response = redirect(url_for("account.overview"))

    def _set_read_key_failure():
        _set_account_status("read_key_delete_failure")

    key_id = request.form.get("key_id")
    if not key_id:
        _set_read_key_failure()
        return response

    user = none_throws(current_user())
    api_key = user.api_read_key(key_id)
    if not api_key:
        _set_read_key_failure()
        return response

    user.delete_api_key(api_key)

    _set_account_status("read_key_delete_success")
    return response


def _set_account_status(status: str) -> None:
    session["account_status"] = status


@blueprint.route("/mytba")
@require_login
def mytba() -> str:
    user = none_throws(current_user())
    mytba = user.myTBA

    mytba_events = EventHelper.sorted_events(mytba.events)
    mytba_teams = sorted(mytba.teams, key=lambda team: team.team_number)

    mytba_event_matches = mytba.event_matches
    mytba_event_matches_events = EventHelper.sorted_events(
        [event_key.get() for event_key in mytba_event_matches.keys()]
    )
    event_matches = [
        (event, MatchHelper.natural_sorted_matches(mytba_event_matches[event.key]))
        for event in mytba_event_matches_events
    ]
    attendance_stats_helper = mytba.attendance_stats_helper

    template_values = {
        "event_fav_sub": [
            (
                event,
                mytba.favorite(ModelType.EVENT, none_throws(event.key.string_id())),
                mytba.subscription(ModelType.EVENT, none_throws(event.key.string_id())),
            )
            for event in mytba_events
        ],
        "team_fav_sub": [
            (
                team,
                mytba.favorite(ModelType.TEAM, none_throws(team.key.string_id())),
                mytba.subscription(ModelType.TEAM, none_throws(team.key.string_id())),
            )
            for team in mytba_teams
        ],
        "event_match_fav_sub": [
            (
                event,
                [
                    (
                        match,
                        mytba.favorite(
                            ModelType.MATCH, none_throws(match.key.string_id())
                        ),
                        mytba.subscription(
                            ModelType.MATCH, none_throws(match.key.string_id())
                        ),
                    )
                    for match in matches
                ],
            )
            for (event, matches) in event_matches
        ],
        "status": request.args.get("status"),
        "year": SeasonHelper.effective_season_year(),
        "attendance_stats_helper": attendance_stats_helper,
    }
    return render_template("mytba.html", **template_values)


@blueprint.get("/mytba/team/<int:team_number>")
@require_login
def mytba_team_get(team_number: TeamNumber) -> str:
    team_key = f"frc{team_number}"
    team = Team.get_by_id(team_key)

    if not team:
        abort(404)

    user = none_throws(current_user())
    favorite = Favorite.query(
        Favorite.model_key == team_key,
        Favorite.model_type == ModelType.TEAM,
        ancestor=none_throws(user.account_key),
    ).get()
    subscription = Subscription.query(
        Favorite.model_key == team_key,
        Favorite.model_type == ModelType.TEAM,
        ancestor=none_throws(user.account_key),
    ).get()

    if not favorite and not subscription:  # New entry; default to being a favorite
        is_favorite = True
    else:
        is_favorite = favorite is not None

    enabled_notifications = [
        (en, NOTIFICATION_RENDER_NAMES[en]) for en in ENABLED_TEAM_NOTIFICATIONS
    ]

    template_values = {
        "team": team,
        "is_favorite": is_favorite,
        "subscription": subscription,
        "enabled_notifications": enabled_notifications,
    }
    return render_template("mytba_team.html", **template_values)


@blueprint.post("/mytba/team/<int:team_number>")
@require_login
def mytba_team_post(team_number: TeamNumber) -> Response:
    team_key = f"frc{team_number}"
    user = none_throws(current_user())

    if request.form.get("favorite"):
        MyTBAHelper.add_favorite(
            Favorite(
                parent=none_throws(user.account_key),
                user_id=none_throws(user.account_key).id(),
                model_type=ModelType.TEAM,
                model_key=team_key,
            )
        )
    else:
        MyTBAHelper.remove_favorite(
            none_throws(user.account_key), team_key, ModelType.TEAM
        )

    subs = request.form.getlist("notification_types")
    if subs:
        MyTBAHelper.add_subscription(
            Subscription(
                parent=none_throws(user.account_key),
                user_id=none_throws(user.account_key).id(),
                model_type=ModelType.TEAM,
                model_key=team_key,
                notification_types=[int(s) for s in subs],
            )
        )
    else:
        MyTBAHelper.remove_subscription(
            none_throws(user.account_key), team_key, ModelType.TEAM
        )

    return safe_next_redirect(
        url_for("account.mytba", _anchor="my-teams", status="team_updated")
    )


@blueprint.get("/mytba/event/<string:event_key>")
@require_login
def mytba_event_get(event_key: EventKey) -> str:
    event = None
    is_wildcard = False

    # Handle wildcard for all events in a year
    if event_key.endswith("*"):
        try:
            year = int(event_key[:-1])
        except ValueError:
            year = None

        if year and year in SeasonHelper.get_valid_years():
            event = Event(  # fake event for rendering
                name="ALL {} EVENTS".format(year),
                year=year,
            )
            is_wildcard = True
    else:
        event = Event.get_by_id(event_key)

    if not event:
        abort(404)

    user = none_throws(current_user())
    favorite = Favorite.query(
        Favorite.model_key == event_key,
        Favorite.model_type == ModelType.EVENT,
        ancestor=none_throws(user.account_key),
    ).get()
    subscription = Subscription.query(
        Favorite.model_key == event_key,
        Favorite.model_type == ModelType.EVENT,
        ancestor=none_throws(user.account_key),
    ).get()

    if not favorite and not subscription:  # New entry; default to being a favorite
        is_favorite = True
    else:
        is_favorite = favorite is not None

    enabled_notifications = [
        (en, NOTIFICATION_RENDER_NAMES[en]) for en in ENABLED_EVENT_NOTIFICATIONS
    ]

    template_values = {
        "event": event,
        "is_wildcard": is_wildcard,
        "is_favorite": is_favorite,
        "subscription": subscription,
        "enabled_notifications": enabled_notifications,
    }
    return render_template("mytba_event.html", **template_values)


@blueprint.post("/mytba/event/<string:event_key>")
@require_login
def mytba_event_post(event_key: EventKey) -> Response:
    user = none_throws(current_user())

    if request.form.get("favorite"):
        MyTBAHelper.add_favorite(
            Favorite(
                parent=none_throws(user.account_key),
                user_id=none_throws(user.account_key).id(),
                model_type=ModelType.EVENT,
                model_key=event_key,
            )
        )
    else:
        MyTBAHelper.remove_favorite(
            none_throws(user.account_key), event_key, ModelType.EVENT
        )

    subs = request.form.getlist("notification_types")
    if subs:
        MyTBAHelper.add_subscription(
            Subscription(
                parent=none_throws(user.account_key),
                user_id=none_throws(user.account_key).id(),
                model_type=ModelType.EVENT,
                model_key=event_key,
                notification_types=[int(s) for s in subs],
            )
        )
    else:
        MyTBAHelper.remove_subscription(
            none_throws(user.account_key), event_key, ModelType.EVENT
        )

    return safe_next_redirect(
        url_for("account.mytba", _anchor="my-events", status="event_updated")
    )


@blueprint.get("/mytba/eventteam/<int:team_number>")
@require_login
def mytba_eventteam_get(team_number: TeamNumber) -> str:
    team = Team.get_by_id(f"frc{team_number}")
    if not team:
        abort(404)

    user = none_throws(current_user())

    team_events = TeamEventsQuery(none_throws(team.key.string_id())).fetch()

    favorites = Favorite.query(
        Favorite.model_type == ModelType.EVENT_TEAM,
        Favorite.model_key.IN(  # pyre-ignore[16]
            [f"{event.key.string_id()}_{team.key.string_id()}" for event in team_events]
        ),
        ancestor=none_throws(user.account_key),
    ).fetch(1000)

    already_favorited = set()
    if favorites:
        already_favorited = {f.model_key for f in favorites}

    template_values = {
        "team": team,
        "team_events": team_events,
        "already_favorited": already_favorited,
    }
    return render_template("mytba_eventteam.html", **template_values)


@blueprint.post("/mytba/eventteam/<int:team_number>")
@require_login
def mytba_eventteam_post(team_number: TeamNumber) -> Response:
    team = Team.get_by_id(f"frc{team_number}")
    if not team:
        abort(404)

    team_key = f"frc{team_number}"

    user = none_throws(current_user())
    team_events = TeamEventsQuery(none_throws(team.key.string_id())).fetch()
    for event in team_events:
        MyTBAHelper.remove_favorite(
            account_key=none_throws(user.account_key),
            model_key=f"{event.key.string_id()}_{team.key.string_id()}",
            model_type=ModelType.EVENT_TEAM,
        )

    favorites = request.form.getlist("favorite_events")
    if favorites:
        for event_key in favorites:
            MyTBAHelper.add_favorite(
                Favorite(
                    parent=none_throws(user.account_key),
                    user_id=none_throws(user.account_key).id(),
                    model_type=ModelType.EVENT_TEAM,
                    model_key=f"{event_key}_{team_key}",
                )
            )

    response = redirect(url_for("account.mytba"))
    return response


@blueprint.route("/ping", methods=["POST"])
@enforce_login
def ping():
    user = none_throws(current_user())
    response = redirect(url_for("account.overview"))

    mobile_client_id = request.form.get("mobile_client_id")

    from backend.common.models.mobile_client import MobileClient

    client = MobileClient.get_by_id(
        int(mobile_client_id), parent=none_throws(user.account_key)
    )
    if client is None:
        session["ping_sent"] = "0"
        return response

    from backend.common.helpers.tbans_helper import TBANSHelper

    success, valid_url = TBANSHelper.ping(client)
    if success:
        session["ping_sent"] = "1"
    else:
        session["ping_sent"] = "0"

    return response


# class myTBAAddHotMatchesController(LoggedInHandler):
#     def get(self, event_key=None):
#         self._require_registration()
#
#         if event_key is None:
#             events = EventHelper.getEventsWithinADay()
#             EventHelper.sorted_events(events)
#             self.template_values['events'] = events
#             self.response.out.write(jinja2_engine.render('mytba_add_hot_matches_base.html', self.template_values))
#             return
#
#         event = Event.get_by_id(event_key)
#         if not event:
#             self.abort(404)
#
#         subscriptions_future = Subscription.query(
#             Subscription.model_type==ModelType.MATCH,
#             Subscription.notification_types==NotificationType.UPCOMING_MATCH,
#             ancestor=self.user_bundle.account.key).fetch_async(projection=[Subscription.model_key])
#
#         matches = []
#         if event.details and event.details.predictions and event.details.predictions['match_predictions']:
#             match_predictions = dict(
#                 event.details.predictions['match_predictions']['qual'].items() +
#                 event.details.predictions['match_predictions']['playoff'].items())
#             max_hotness = 0
#             min_hotness = float('inf')
#             for match in event.matches:
#                 if not match.has_been_played and match.key.id() in match_predictions:
#                     prediction = match_predictions[match.key.id()]
#                     red_score = prediction['red']['score']
#                     blue_score = prediction['blue']['score']
#                     if red_score > blue_score:
#                         winner_score = red_score
#                         loser_score = blue_score
#                     else:
#                         winner_score = blue_score
#                         loser_score = red_score
#
#                     hotness = winner_score + 2.0*loser_score  # Favor close high scoring matches
#
#                     max_hotness = max(max_hotness, hotness)
#                     min_hotness = min(min_hotness, hotness)
#                     match.hotness = hotness
#                     matches.append(match)
#
#         existing_subscriptions = set()
#         for sub in subscriptions_future.get_result():
#             existing_subscriptions.add(sub.model_key)
#
#         hot_matches = []
#         for match in matches:
#             match.hotness = 100 * (match.hotness - min_hotness) / (max_hotness - min_hotness)
#             match.already_subscribed = match.key.id() in existing_subscriptions
#             hot_matches.append(match)
#         hot_matches = sorted(hot_matches, key=lambda match: -match.hotness)
#         matches_dict = {'qm': hot_matches[:25]}
#
#         self.template_values['event'] = event
#         self.template_values['matches'] = matches_dict
#
#         self.response.out.write(jinja2_engine.render('mytba_add_hot_matches.html', self.template_values))
#
#     def post(self, event_key):
#         self._require_registration()
#
#         current_user_id = self.user_bundle.account.key.id()
#
#         event = Event.get_by_id(event_key)
#         subscribed_matches = set(self.request.get_all('subscribed_matches'))
#
#         for match in event.matches:
#             if not match.has_been_played:
#                 match_key = match.key.id()
#                 if match.key.id() in subscribed_matches:
#                     sub = Subscription(
#                         parent=ndb.Key(Account, current_user_id),
#                         user_id=current_user_id,
#                         model_type=ModelType.MATCH,
#                         model_key=match_key,
#                         notification_types=[NotificationType.UPCOMING_MATCH]
#                     )
#                     MyTBAHelper.add_subscription(sub)
#                 else:
#                     MyTBAHelper.remove_subscription(current_user_id, match_key, ModelType.MATCH)
#
#         self.redirect('/account/mytba?status=match_updated#my-matches'.format(event_key))
#
#
# class MyTBAMatchController(LoggedInHandler):
#     def get(self, match_key):
#         self._require_registration()
#
#         match = Match.get_by_id(match_key)
#
#         if not match:
#             self.abort(404)
#
#         user = self.user_bundle.account.key
#         favorite = Favorite.query(Favorite.model_key==match_key, Favorite.model_type==ModelType.MATCH, ancestor=user).get()
#         subscription = Subscription.query(Favorite.model_key==match_key, Favorite.model_type==ModelType.MATCH, ancestor=user).get()
#
#         if not favorite and not subscription:  # New entry; default to being a favorite
#             is_favorite = True
#         else:
#             is_favorite = favorite is not None
#
#         enabled_notifications = [(en, NotificationType.render_names[en]) for en in NotificationType.enabled_match_notifications]
#
#         self.template_values['match'] = match
#         self.template_values['is_favorite'] = is_favorite
#         self.template_values['subscription'] = subscription
#         self.template_values['enabled_notifications'] = enabled_notifications
#
#         self.response.out.write(jinja2_engine.render('mytba_match.html', self.template_values))
#
#     def post(self, match_key):
#         self._require_registration()
#
#         current_user_id = self.user_bundle.account.key.id()
#         match = Match.get_by_id(match_key)
#
#         if self.request.get('favorite'):
#             favorite = Favorite(
#                 parent=ndb.Key(Account, current_user_id),
#                 user_id=current_user_id,
#                 model_type=ModelType.MATCH,
#                 model_key=match_key
#             )
#             MyTBAHelper.add_favorite(favorite)
#         else:
#             MyTBAHelper.remove_favorite(current_user_id, match_key, ModelType.MATCH)
#
#         subs = self.request.get_all('notification_types')
#         if subs:
#             subscription = Subscription(
#                 parent=ndb.Key(Account, current_user_id),
#                 user_id=current_user_id,
#                 model_type=ModelType.MATCH,
#                 model_key=match_key,
#                 notification_types=[int(s) for s in subs]
#             )
#             MyTBAHelper.add_subscription(subscription)
#         else:
#             MyTBAHelper.remove_subscription(current_user_id, match_key, ModelType.MATCH)
#
#         self.redirect('/account/mytba?status=match_updated#my-matches')
