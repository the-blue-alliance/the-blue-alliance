import datetime
from typing import Optional

from flask import abort, request
from google.appengine.ext import ndb

from backend.common.consts.comp_level import COMP_LEVELS, COMP_LEVELS_VERBOSE_FULL
from backend.common.consts.playoff_type import TYPE_NAMES as PLAYOFF_TYPE_NAMES
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
from backend.common.models.media import Media
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.web.profiled_render import render_template


def event_list(year: Optional[Year]) -> str:
    if year is None:
        year = datetime.datetime.now().year

    events = Event.query(Event.year == year).order(Event.start_date).fetch(10000)

    template_values = {
        "valid_years": SeasonHelper.get_valid_years(),
        "selected_year": year,
        "events": events,
    }

    return render_template("admin/event_list.html", template_values)


def event_detail(event_key: EventKey) -> str:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)
    event.prep_awards_matches_teams()

    reg_sitevar = ChampsRegistrationHacks.get()
    api_keys = ApiAuthAccess.query(
        ApiAuthAccess.event_list == ndb.Key(Event, event_key)
    ).fetch()
    event_medias = Media.query(Media.references == event.key).fetch(500)
    playoff_template = PlayoffAdvancementHelper.playoff_template(event)
    elim_bracket_html = render_template(
        "bracket_partials/bracket_table.html",
        {"bracket_table": event.playoff_bracket, "event": event},
    )
    advancement_html = (
        render_template(
            "playoff_partials/{}.html".format(playoff_template),
            {
                "event": event,
                "playoff_advancement": event.playoff_advancement,
                "playoff_advancement_tiebreakers": PlayoffAdvancementHelper.ROUND_ROBIN_TIEBREAKERS.get(
                    event.year
                ),
                "bracket_table": event.playoff_bracket,
            },
        )
        if playoff_template
        else "None"
    )

    _, organized_matches = MatchHelper.organized_matches(event.matches)
    match_stats = []
    for comp_level in COMP_LEVELS:
        level_matches = organized_matches[comp_level]
        if not level_matches:
            continue
        match_stats.append(
            {
                "comp_level": comp_level,
                "level_name": COMP_LEVELS_VERBOSE_FULL[comp_level],
                "total": len(level_matches),
                "played": len(list(filter(lambda m: m.has_been_played, level_matches))),
                "unplayed": len(
                    list(filter(lambda m: not m.has_been_played, level_matches))
                ),
            }
        )

    template_values = {
        "event": event,
        "medias": event_medias,
        "flushed": request.args.get("flushed"),
        "playoff_types": PLAYOFF_TYPE_NAMES,
        "write_auths": api_keys,
        "event_sync_disable": event_key in reg_sitevar["divisions_to_skip"],
        "set_start_day_to_last": event_key in reg_sitevar["set_start_to_last_day"],
        "skip_eventteams": event_key in reg_sitevar["skip_eventteams"],
        "event_name_override": next(
            iter(
                filter(
                    lambda e: e.get("event") == event_key,
                    reg_sitevar["event_name_override"],
                )
            ),
            {},
        ).get("name", ""),
        "elim_bracket_html": elim_bracket_html,
        "advancement_html": advancement_html,
        "match_stats": match_stats,
        "deleted_count": request.args.get("deleted"),
    }

    return render_template("admin/event_details.html", template_values)


"""
# todo: haven't ported the event/<event_key>/edit page yet
def event_detail_post(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    reg_sitevar = ChampsRegistrationHacks.get()

    new_divisions_to_skip = reg_sitevar["divisions_to_skip"]
    if request.form.get("event_sync_disable"):
        if event_key not in new_divisions_to_skip:
            new_divisions_to_skip.append(event_key)
    else:
        new_divisions_to_skip = list(
            filter(lambda e: e != event_key, new_divisions_to_skip)
        )

    new_start_day_to_last = reg_sitevar["set_start_to_last_day"]
    if request.form.get("set_start_day_to_last"):
        if event_key not in new_start_day_to_last:
            new_start_day_to_last.append(event_key)
    else:
        new_start_day_to_last = list(
            filter(lambda e: e != event_key, new_start_day_to_last)
        )

    new_skip_eventteams = reg_sitevar["skip_eventteams"]
    if request.form.get("skip_eventteams"):
        if event_key not in new_skip_eventteams:
            new_skip_eventteams.append(event_key)
    else:
        new_skip_eventteams = list(
            filter(lambda e: e != event_key, new_skip_eventteams)
        )

    new_name_overrides = reg_sitevar["event_name_override"]
    if request.form.get("event_name_override"):
        if not any(o["event"] == event_key for o in new_name_overrides):
            new_name_overrides.append(
                {
                    "event": event_key,
                    "name": request.form.get("event_name_override"),
                    "short_name": request.form.get("event_name_override"),
                }
            )
    else:
        new_name_overrides = list(
            filter(lambda o: o["event"] != event_key, new_name_overrides)
        )

    ChampsRegistrationHacks.put(
        {
            "divisions_to_skip": new_divisions_to_skip,
            "set_start_to_last_day": new_start_day_to_last,
            "skip_eventteams": new_skip_eventteams,
            "event_name_override": new_name_overrides,
        }
    )

    return redirect(url_for("admin.event_detail", event_key=event_key))
"""
