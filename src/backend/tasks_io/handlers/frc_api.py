import re
from typing import List, Optional, Set

from flask import (
    Blueprint,
    escape,
    make_response,
    render_template,
    request,
    Response,
    url_for,
)
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.helpers.listify import listify
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


blueprint = Blueprint("frc_api", __name__)


# @blueprint.route("/awards")
# @blueprint.route("/awards/<int:from backend.common.helpers.listify import delistify, listifyyear>")
# TODO: Drop support for this "now" and just use an empty year
@blueprint.route("/tasks/enqueue/fmsapi_awards/now", defaults={"year": None})
@blueprint.route("/tasks/enqueue/fmsapi_awards/<int:year>")
def awards_year(year: Optional[int]) -> Response:
    events: List[Event]
    if year is None:
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official, events))
    else:
        event_keys = (
            Event.query(Event.official == True)  # noqa: E712
            .filter(Event.year == year)
            .fetch(keys_only=True)
        )
        events = ndb.get_multi(event_keys)

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            url=url_for("frc_api.awards_event", event_key=event.key_name),
            method="GET",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/fmsapi_awards_enqueue.html", events=events)
        )

    return make_response("")


# @blueprint.route("/awards/<event_key>")
@blueprint.route("/tasks/get/fmsapi_awards/<event_key>")
def awards_event(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key) if Event.validate_key_name(event_key) else None
    if event is None:
        return make_response(f"No Event for key: {escape(event_key)}", 404)

    datafeed = DatafeedFMSAPI()
    awards = datafeed.get_awards(event)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_awards(awards, event.remap_teams)

    new_awards = AwardManipulator.createOrUpdate(awards)
    # new_awards could be a single object or None
    new_awards = listify(new_awards)

    # Create EventTeams
    team_ids: Set[TeamKey] = set()
    for award in new_awards:
        for team in award.team_list:
            team_id = none_throws(team.string_id())
            # strip all suffixes (eg B teams)
            team_ids.add("frc" + re.sub("[^0-9]", "", team_id))

    teams = TeamManipulator.createOrUpdate(
        [Team(id=team_id, team_number=int(team_id[3:])) for team_id in team_ids]
    )

    if teams:
        # teams might be a single object
        teams = listify(teams)

        EventTeamManipulator.createOrUpdate(
            [
                EventTeam(
                    id=event_key + "_" + team.key_name,
                    event=event.key,
                    team=team.key,
                    year=event.year,
                )
                for team in teams
            ]
        )

    # Only write out if not in taskqueue
    if "X-Appengine-Taskname" not in request.headers:
        return make_response(
            render_template("datafeeds/fmsapi_awards_get.html", awards=new_awards)
        )

    return make_response("")
