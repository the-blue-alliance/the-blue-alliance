from datetime import datetime, timedelta
from typing import Any, Callable, cast, Dict, Optional, Tuple

from flask import abort, Response
from google.appengine.ext import ndb

from backend.common.consts.event_type import CMP_EVENT_TYPES
from backend.common.consts.landing_type import LandingType
from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.team_helper import TeamHelper
from backend.common.memcache import MemcacheClient
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.common.models.media import Media
from backend.common.sitevars.landing_config import LandingConfig
from backend.web.profiled_render import render_template


@cached_public
def index() -> Response:
    HANDLER_MAP: Dict[
        LandingType, Tuple[Callable[[Dict[str, Any]], str], timedelta]
    ] = {
        # map landing type -> (handler function, cache ttl)
        LandingType.KICKOFF: (index_kickoff, timedelta(minutes=5)),
        LandingType.BUILDSEASON: (index_buildseason, timedelta(minutes=5)),
        LandingType.COMPETITIONSEASON: (
            index_competitionseason,
            timedelta(minutes=5),
        ),
        LandingType.CHAMPS: (index_champs, timedelta(minutes=5)),
        LandingType.OFFSEASON: (index_offseason, timedelta(minutes=5)),
        LandingType.INSIGHTS: (index_insights, timedelta(minutes=5)),
    }
    landing_type = LandingConfig.current_landing_type()
    landing_type_handler, cache_ttl = HANDLER_MAP[landing_type]
    template_values = cast(Dict[str, Any], LandingConfig.get())
    return make_cached_response(landing_type_handler(template_values), ttl=cache_ttl)


def index_kickoff(template_values: Dict[str, Any]) -> str:
    # special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()
    template_values.update(
        {
            "year": effective_season_year,
            "is_kickoff": SeasonHelper.is_kickoff_at_least_one_day_away(
                year=effective_season_year
            ),
            "kickoff_datetime_est": SeasonHelper.kickoff_datetime_est(
                effective_season_year
            ),
            "kickoff_datetime_utc": SeasonHelper.kickoff_datetime_utc(
                effective_season_year
            ),
        }
    )
    # "events": EventHelper.week_events(),
    # "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
    # "special_webcasts": special_webcasts
    return render_template("index/index_kickoff.html", template_values)


def index_buildseason(template_values: Dict[str, Any]) -> str:
    special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()
    template_values.update(
        {
            "year": effective_season_year,
            "seasonstart_datetime_utc": SeasonHelper.first_event_datetime_utc(
                effective_season_year
            ),
            "events": EventHelper.week_events(),
            "any_webcast_online": any(
                w.get("status") == "online" for w in special_webcasts
            ),
            "special_webcasts": special_webcasts,
        }
    )
    return render_template("index/index_buildseason.html", template_values)


def index_competitionseason(template_values: Dict[str, Any]) -> str:
    week_events = EventHelper.week_events()
    popular_teams_events = TeamHelper.getPopularTeamsEvents(week_events)

    # Only show special webcasts that aren't also hosting an event
    special_webcasts = []
    for special_webcast in FirebasePusher.get_special_webcasts():
        add = True
        for event in week_events:
            if event.now and event.webcast:
                for event_webcast in event.webcast:
                    if (
                        special_webcast.get("type", "") == event_webcast.get("type", "")
                        and special_webcast.get("channel", "")
                        == event_webcast.get("channel", "")
                        and special_webcast.get("file", "")
                        == event_webcast.get("file", "")
                    ):
                        add = False
                        break
            if not add:
                break
        if add:
            special_webcasts.append(special_webcast)

    template_values.update(
        {
            "events": week_events,
            "any_webcast_online": any(
                w.get("status") == "online" for w in special_webcasts
            ),
            "special_webcasts": special_webcasts,
            "popular_teams_events": popular_teams_events,
        }
    )
    return render_template("index/index_competitionseason.html", template_values)


def index_champs(template_values: Dict[str, Any]) -> str:
    year = datetime.now().year
    event_keys_future = Event.query(
        Event.year == year, Event.event_type_enum.IN(CMP_EVENT_TYPES)
    ).fetch_async(keys_only=True)

    events_futures = ndb.get_multi_async(event_keys_future.get_result())

    template_values.update(
        {
            "events": [e.get_result() for e in events_futures],
            "year": year,
        }
    )
    return render_template("index/index_champs.html", template_values)


def index_offseason(template_values: Dict[str, Any]) -> str:
    special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()

    template_values.update(
        {
            "year": effective_season_year,
            "events": EventHelper.week_events(),
            "kickoff_datetime_utc": SeasonHelper.kickoff_datetime_utc(
                effective_season_year
            ),
            "any_webcast_online": any(
                w.get("status") == "online" for w in special_webcasts
            ),
            "special_webcasts": special_webcasts,
        }
    )
    return render_template("index/index_offseason.html", template_values)


def index_insights(template_values: Dict[str, Any]) -> str:
    week_events = EventHelper.week_events()
    year = datetime.now().year
    special_webcasts = FirebasePusher.get_special_webcasts()
    template_values.update(
        {
            "events": week_events,
            "year": year,
            "any_webcast_online": any(
                w.get("status") == "online" for w in special_webcasts
            ),
            "special_webcasts": special_webcasts,
        }
    )

    insights = ndb.get_multi(
        [
            ndb.Key(Insight, Insight.render_key_name(year, insight_name))
            for insight_name in Insight.INSIGHT_NAMES.values()
        ]
    )
    for insight in insights:
        if insight:
            template_values[insight.name] = insight

    return render_template("index/index_insights.html", template_values)


@cached_public
def about() -> str:
    return render_template("about.html")


@cached_public(ttl=timedelta(hours=24))
def avatar_list(year: Optional[Year] = None) -> Response:
    year = year or SeasonHelper.get_current_season()

    valid_years = list(range(2018, SeasonHelper.get_max_year() + 1))
    valid_years.remove(2021)  # No avatars in 2021 :(

    if year not in valid_years:
        abort(404)

    memcache = MemcacheClient.get()

    avatars = []
    shards = memcache.get_multi(
        [f"{year}avatars_{i}".encode("utf-8") for i in range(10)]
    )
    if len(shards) == 10:  # If missing a shard, must refetch all
        for _, shard in sorted(shards.items(), key=lambda kv: kv[0]):
            avatars += shard

    if not avatars:
        avatars_future = Media.query(
            Media.media_type_enum == MediaType.AVATAR, Media.year == year
        ).fetch_async()
        avatars = avatars_future.get_result()
        avatars = filter(lambda a: len(a.references) > 0, avatars)
        avatars = sorted(avatars, key=lambda a: int(a.references[0].id()[3:]))

        shards = {}
        size = len(avatars) / 10 + 1
        for i in range(10):
            start = i * size
            end = start + size
            shards[f"{year}avatars_{i}"] = avatars[int(start) : int(end)]
        memcache.set_multi(shards, 60 * 60 * 24)

    template_values = {
        "year": year,
        "valid_years": valid_years,
        "avatars": avatars,
    }

    return render_template("avatars.html", template_values)
