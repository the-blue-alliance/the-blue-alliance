from datetime import timedelta
from typing import Any, Callable, cast, Dict, Tuple

from flask import Response

from backend.common.consts.landing_type import LandingType
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.event_helper import EventHelper

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.sitevars.landing_config import LandingConfig
from backend.web.profiled_render import render_template


@cached_public
def index() -> int:
    HANDLER_MAP: Dict[
        LandingType, Tuple[Callable[[Dict[str, Any]], str], timedelta]
    ] = {
        # map landing type -> (handler function, cache ttl)
        LandingType.KICKOFF: (index_kickoff, timedelta(days=1)),
        LandingType.BUILDSEASON: (index_buildseason, timedelta(minutes=5)),
        LandingType.COMPETITIONSEASON: (
            index_competitionseason,
            timedelta(minutes=5),
        ),
        LandingType.CHAMPS: (index_champs, timedelta(minutes=5)),
        LandingType.OFFSEASON: (index_offseason, timedelta(days=1)),
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
    # special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()
    template_values.update(
        {
            "year": effective_season_year,
            "seasonstart_datetime_utc": SeasonHelper.first_event_datetime_utc(
                effective_season_year
            ),
        }
    )
    # "events": EventHelper.week_events(),
    # "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
    # "special_webcasts": special_webcasts,
    return render_template("index/index_buildseason.html", template_values)

def index_competitionseason(template_values: Dict[str, Any]) -> str:
    # week_events = EventHelper.week_events()
    # popular_teams_events = TeamHelper.getPopularTeamsEvents(week_events)
    #
    # # Only show special webcasts that aren't also hosting an event
    # special_webcasts = []
    # for special_webcast in FirebasePusher.get_special_webcasts():
    #     add = True
    #     for event in week_events:
    #         if event.now and event.webcast:
    #             for event_webcast in event.webcast:
    #                 if (special_webcast.get('type', '') == event_webcast.get('type', '') and
    #                         special_webcast.get('channel', '') == event_webcast.get('channel', '') and
    #                         special_webcast.get('file', '') == event_webcast.get('file', '')):
    #                     add = False
    #                     break
    #         if not add:
    #             break
    #     if add:
    #         special_webcasts.append(special_webcast)
    #
    # template_values.update({
    #     "events": week_events,
    #     "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
    #     "special_webcasts": special_webcasts,
    #     "popular_teams_events": popular_teams_events,
    # })
    return render_template("index/index_competitionseason.html", template_values)


def index_champs(template_values: Dict[str, Any]) -> str:
    # year = datetime.datetime.now().year
    # hou_event_keys_future = Event.query(
    #     Event.year == year,
    #     Event.event_type_enum.IN(EventType.CMP_EVENT_TYPES),
    #     Event.start_date <= datetime.datetime(2019, 4, 21)).fetch_async(keys_only=True)
    # det_event_keys_future = Event.query(
    #     Event.year == year,
    #     Event.event_type_enum.IN(EventType.CMP_EVENT_TYPES),
    #     Event.start_date > datetime.datetime(2019, 4, 21)).fetch_async(keys_only=True)
    #
    # hou_events_futures = ndb.get_multi_async(hou_event_keys_future.get_result())
    # det_events_futures = ndb.get_multi_async(det_event_keys_future.get_result())
    #
    # template_values.update({
    #     "hou_events": [e.get_result() for e in hou_events_futures],
    #     "det_events": [e.get_result() for e in det_events_futures],
    #     "year": year,
    # })
    return render_template("index/index_champs.html", template_values)


def index_offseason(template_values: Dict[str, Any]) -> str:
    # special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()

    template_values.update(
        {
            "events": EventHelper.week_events(),
            "kickoff_datetime_utc": SeasonHelper.kickoff_datetime_utc(
                effective_season_year
            ),
            # "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            # "special_webcasts": special_webcasts,
        }
    )
    return render_template("index/index_offseason.html", template_values)


def index_insights(template_values: Dict[str, Any]) -> str:
    # week_events = EventHelper.week_events()
    # year = datetime.datetime.now().year
    # special_webcasts = FirebasePusher.get_special_webcasts()
    # template_values.update({
    #     "events": week_events,
    #     "year": year,
    #     "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
    #     "special_webcasts": special_webcasts,
    # })
    #
    # insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
    # for insight in insights:
    #     if insight:
    #         self.template_values[insight.name] = insight
    #
    return render_template("index/index_insights.html", template_values)


@cached_public
def about() -> int:
    return render_template("about.html")
