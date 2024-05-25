from typing import Dict, List, Set

from firebase_admin import db as firebase_db
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from backend.common.environment import Environment
from backend.common.firebase import app as get_firebase_app
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.webcast_online_helper import WebcastOnlineHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.match import Match
from backend.common.models.webcast import Webcast
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import (
    MatchConverter,
    MatchDict,
)
from backend.common.sitevars.forced_live_events import ForcedLiveEvents
from backend.common.sitevars.gameday_special_webcasts import GamedaySpecialWebcasts


class FirebasePusher:
    DB_URL = "https://{project}.firebaseio.com/"

    @classmethod
    def _get_reference(cls, key: str) -> firebase_db.Reference:
        url = cls.DB_URL.format(project=Environment.project())
        return firebase_db.reference(key, app=get_firebase_app(), url=url)

    @classmethod
    def _delete_data(cls, key: str) -> None:
        """
        Remove data from the specified Firebase database reference.
        """
        ref = cls._get_reference(key)
        ref.delete()

    @classmethod
    def _patch_data(cls, key: str, data: Dict) -> None:
        """
        Write or replace data to a defined path, like messages/users/user1/<data>
        """
        ref = cls._get_reference(key)
        ref.update(data)

    @classmethod
    def _put_data(cls, key: str, data: Dict) -> None:
        """
        Write or replace data to a defined path, like messages/users/user1/<data>
        """
        ref = cls._get_reference(key)
        ref.set(data)

    """
    @classmethod
    def _push_data(cls, key: str, data_json: str) -> None:
        \"""
        Add to a list of data in our Firebase database.
        Every time we send a POST request, the Firebase client generates a unique key, like messages/users/<unique-id>/<data>
        \"""
        ref = cls._get_reference(key)
        ref.push(data_json)
    """

    @classmethod
    def delete_match(cls, match: Match) -> None:
        """
        Deletes a match from an event and event_team
        """
        deferred.defer(
            cls._delete_data,
            f"e/{match.event_key_name}/m/{match.short_key}",
            _target="py3-tasks-io",
            _queue="firebase",
            _url="/_ah/queue/deferred_firebase_delete_match",
        )

        # for team_key_name in match.team_key_names:
        #     deferred.defer(
        #     cls._delete_data,
        #     'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #     _queue="firebase")

    @classmethod
    def _construct_match_dict(cls, match: MatchDict) -> Dict:
        """
        Minimal amount needed to render
        """
        match_dict = {
            "c": match["comp_level"],
            "s": match["set_number"],
            "m": match["match_number"],
            "r": match["alliances"]["red"]["score"],
            "rt": match["alliances"]["red"]["team_keys"],
            "b": match["alliances"]["blue"]["score"],
            "bt": match["alliances"]["blue"]["team_keys"],
            "t": match["time"],
            "pt": match["predicted_time"],
            "w": match["winning_alliance"],
        }
        return match_dict

    """
    @classmethod
    def replace_event_matches(cls, event_key: EventKey, matches: List[Match]) -> None:
        \"""
        Deletes matches from an event and puts these instead
        \"""

        match_data = {}
        for match in matches:
            match_data[match.short_key] = cls._construct_match_dict(
                MatchConverter.matchConverter_v3(match)
            )
        deferred.defer(
            cls._put_data,
            f"e/{event_key}/m",
            json.dumps(match_data),
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_replace_event_matches",
        )
    """

    @classmethod
    def update_match(cls, match: Match, updated_attrs: Set[str]) -> None:
        """
        Updates a match in an event and event/team
        """
        if match.year < 2017:
            return

        if "predicted_time" in updated_attrs:
            # Hacky way of preventing predicted time updates from clobbering scores
            match_dict = {
                "pt": MatchConverter.matchConverter_v3(match)["predicted_time"],
            }
        else:
            match_dict = cls._construct_match_dict(
                MatchConverter.matchConverter_v3(match)
            )

        deferred.defer(
            cls._patch_data,
            "e/{}/m/{}".format(match.event.id(), match.short_key),
            match_dict,
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_match",
        )

        # for team_key_name in match.team_key_names:
        #     deferred.defer(
        #         cls._put_data,
        #         'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #         match_data_json,
        #         _queue="firebase")

    """
    @classmethod
    def update_event_details(cls, event_details: EventDetails) -> None:
        \"""
        Updates an event_detail in an event
        \"""
        return
        # if int(event_details.key.id()[:4]) < 2017:
        #     return

        # event_details_json = json.dumps(EventDetailsConverter.convert(event_details, 3))

        # deferred.defer(
        #     cls._patch_data,
        #     'events/{}/details'.format(event_details.key.id()),
        #     event_details_json,
        #     _queue="firebase")

    @classmethod
    def update_event_team_status(
        cls, event_key: EventKey, team_key: TeamKey, status: EventTeamStatus
    ):
        \"""
        Updates an event team status
        \"""
        return
        # if int(event_key[:4]) < 2017:
        #     return

        # from helpers.event_team_status_helper import EventTeamStatusHelper  # Prevent circular import

        # if status:
        #     status.update({
        #         'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
        #         'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
        #         'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
        #     })

        # status_json = json.dumps(status)

        # deferred.defer(
        #     cls._put_data,
        #     'event_teams/{}/{}/status'.format(event_key, team_key),
        #     status_json,
        #     _queue="firebase")
    """

    @classmethod
    def update_live_events(cls) -> None:
        """
        Updates live_events and special webcasts
        """
        events_by_key: Dict[EventKey, Dict] = {}
        for event_key, event in cls._update_live_events_helper().items():
            converted_event = EventConverter.eventConverter_v3(event)
            # Only what's needed to render webcast
            partial_event = {
                key: converted_event[key]
                for key in ["key", "name", "short_name", "webcasts"]
            }
            # Hack in district code
            if event.district_key and partial_event.get("short_name"):
                partial_event["short_name"] = "[{}] {}".format(
                    event.district_key.id()[4:].upper(), partial_event["short_name"]
                )

            events_by_key[event_key] = partial_event

        deferred.defer(
            cls._put_data,
            "live_events",
            events_by_key,
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_live_events",
        )

        deferred.defer(
            cls._put_data,
            "special_webcasts",
            cls.get_special_webcasts(),
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_special_webcasts",
        )

    @classmethod
    @ndb.toplevel
    def _update_live_events_helper(cls) -> Dict[EventKey, Dict]:
        week_events = EventHelper.week_events()
        events_by_key: Dict[EventKey, Dict] = {}
        live_events: List[Event] = []
        for event in week_events:
            if event.now:
                event._webcast = event.current_webcasts  # Only show current webcasts
                for webcast in event.webcast:
                    WebcastOnlineHelper.add_online_status_async(webcast)
                events_by_key[event.key.id()] = event
            if event.within_a_day:
                live_events.append(event)

        # To get Champ events to show up before they are actually going on
        forced_live_events = ForcedLiveEvents.get()
        for event in ndb.get_multi(
            [ndb.Key(Event, ekey) for ekey in forced_live_events]
        ):
            if event.webcast:
                for webcast in event.webcast:
                    WebcastOnlineHelper.add_online_status_async(webcast)
            events_by_key[event.key.id()] = event

        # # Add in the Fake TBA BlueZone event (watch for circular imports)
        # from helpers.bluezone_helper import BlueZoneHelper
        # bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        # if bluezone_event:
        #     for webcast in bluezone_event.webcast:
        #         WebcastOnlineHelper.add_online_status_async(webcast)
        #     events_by_key[bluezone_event.key_name] = bluezone_event

        return events_by_key

    @classmethod
    @ndb.toplevel
    def get_special_webcasts(
        cls,
    ) -> List[Webcast]:  # TODO: Break this out of FirebasePusher 2017-03-01 -fangeugene
        special_webcasts: List[Webcast] = []
        for webcast in GamedaySpecialWebcasts.webcasts():
            WebcastOnlineHelper.add_online_status_async(webcast)
            special_webcasts.append(webcast)

        return special_webcasts

    """
    @classmethod
    def update_event(cls, event: Event) -> None:
        WebcastOnlineHelper.add_online_status(event.webcast)

        converted_event = EventConverter.eventConverter_v3(event)
        deferred.defer(
            cls._patch_data,
            "live_events/{}".format(event.key_name),
            json.dumps(
                {
                    key: converted_event[key]
                    for key in ["key", "name", "short_name", "webcasts"]
                }
            ),
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_event",
        )
    """
