import json
import logging

from flask import Blueprint, make_response, render_template, request, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.models.typeahead_entry import TypeaheadEntry

blueprint = Blueprint("typeahead", __name__)


@blueprint.route("/backend-tasks-b2/math/enqueue/typeaheadcalc")
def enqueue_typeahead() -> Response:
    """
    Enqueues typeahead calculation
    """
    taskqueue.add(
        url=url_for("typeahead.do_typeahead"),
        method="GET",
        target="py3-tasks-cpu",
        queue_name="default",
    )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(render_template("math/typeaheadcalc_enqueue.html"))
    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/typeaheadcalc")
def do_typeahead() -> Response:
    """
    Calculates typeahead entries
    """

    @ndb.tasklet
    def get_events_async():
        event_keys = (
            yield Event.query()
            .order(-Event.year)
            .order(Event.name)
            .fetch_async(keys_only=True)
        )
        events = yield ndb.get_multi_async(event_keys)
        raise ndb.Return(events)

    @ndb.tasklet
    def get_teams_async():
        team_keys = (
            yield Team.query().order(Team.team_number).fetch_async(keys_only=True)
        )
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)

    @ndb.tasklet
    def get_districts_async():
        district_keys = (
            yield District.query().order(-District.year).fetch_async(keys_only=True)
        )
        districts = yield ndb.get_multi_async(district_keys)
        raise ndb.Return(districts)

    @ndb.toplevel
    def get_events_teams_districts():
        events, teams, districts = (
            yield get_events_async(),
            get_teams_async(),
            get_districts_async(),
        )
        raise ndb.Return((events, teams, districts))

    events, teams, districts = get_events_teams_districts()

    results = {}
    for team in teams:
        if not team.nickname:
            nickname = "Team %s" % team.team_number
        else:
            nickname = team.nickname
        data = "%s | %s" % (team.team_number, nickname)
        if TypeaheadEntry.ALL_TEAMS_KEY in results:
            results[TypeaheadEntry.ALL_TEAMS_KEY].append(data)
        else:
            results[TypeaheadEntry.ALL_TEAMS_KEY] = [data]

    for district in districts:
        data = "%s District [%s]" % (
            district.display_name,
            district.abbreviation.upper(),
        )
        # all districts
        if TypeaheadEntry.ALL_DISTRICTS_KEY in results:
            if data not in results[TypeaheadEntry.ALL_DISTRICTS_KEY]:
                results[TypeaheadEntry.ALL_DISTRICTS_KEY].append(data)
        else:
            results[TypeaheadEntry.ALL_DISTRICTS_KEY] = [data]

    for event in events:
        data = "%s %s [%s]" % (event.year, event.name, event.event_short.upper())
        # all events
        if TypeaheadEntry.ALL_EVENTS_KEY in results:
            results[TypeaheadEntry.ALL_EVENTS_KEY].append(data)
        else:
            results[TypeaheadEntry.ALL_EVENTS_KEY] = [data]
        # events by year
        if TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year) in results:
            results[TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year)].append(data)
        else:
            results[TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year)] = [data]

    # Prepare to remove old entries
    old_entry_keys_future = TypeaheadEntry.query().fetch_async(keys_only=True)

    # Add new entries
    entries = []
    for key_name, data in results.items():
        entries.append(TypeaheadEntry(id=key_name, data_json=json.dumps(data)))
    ndb.put_multi(entries)

    # Remove old entries
    old_entry_keys = set(old_entry_keys_future.get_result())
    new_entry_keys = set(
        [ndb.Key(TypeaheadEntry, key_name) for key_name in results.keys()]
    )
    keys_to_delete = old_entry_keys.difference(new_entry_keys)
    logging.info(
        "Removing the following unused TypeaheadEntries: {}".format(
            [key.id() for key in keys_to_delete]
        )
    )
    ndb.delete_multi(keys_to_delete)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/typeaheadcalc_do.html", results=results)
        )
    return make_response("")
