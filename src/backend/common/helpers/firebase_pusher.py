from typing import Dict, List, Set

from firebase_admin import db as firebase_db
from pyre_extensions import none_throws

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.environment import Environment
from backend.common.firebase import app as get_firebase_app
from backend.common.helpers.deferred import defer_safe
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    NexusMatchStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.keys import EventKey
from backend.common.models.match import Match
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import (
    MatchConverter,
    MatchDict,
)
from backend.common.sitevars.gameday_special_webcasts import (
    WebcastType as TSpecialWebcast,
)


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
        defer_safe(
            cls._delete_data,
            f"e/{match.event_key_name}/m/{match.short_key}",
            _target="py3-tasks-io",
            _queue="firebase",
            _url=f"/_ah/queue/deferred_firebase_delete_match:{match.key_name}",
        )

        # for team_key_name in match.team_key_names:
        #     defer_safe(
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
        defer_safe(
            cls._put_data,
            f"e/{event_key}/m",
            json.dumps(match_data),
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_replace_event_matches",
        )
    """

    @classmethod
    def update_match(
        cls,
        match: Match,
        updated_attrs: Set[str],
    ) -> None:
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

        defer_safe(
            cls._patch_data,
            "e/{}/m/{}".format(match.event.id(), match.short_key),
            match_dict,
            _queue="firebase",
            _target="py3-tasks-io",
            _url=f"/_ah/queue/deferred_firebase_update_match:{match.key_name}",
        )

        # for team_key_name in match.team_key_names:
        #     defer_safe(
        #         cls._put_data,
        #         'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #         match_data_json,
        #         _queue="firebase")

    @classmethod
    def update_match_queue_status(
        cls, match: Match, nexus_status: EventQueueStatus
    ) -> None:
        if match_status := nexus_status["matches"].get(match.key_name):
            mc = NexusMatchStatusMemcache(match.key_name)
            old_status = mc.get()
            new_status = NexusMatchStatus(match_status["status"])
            mc.put(new_status)

            if old_status == new_status:
                return

            event_key = none_throws(match.event.string_id())
            match_short = match.short_key
            update_dict = {"q": new_status.to_string()}
            defer_safe(
                cls._patch_data,
                f"e/{event_key}/m/{match_short}",
                update_dict,
                _queue="firebase",
                _target="py3-tasks-io",
                _url=f"/_ah/queue/deferred_firebase_update_match_queue_status:{match.key_name}",
            )

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

        # defer_safe(
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

        # defer_safe(
        #     cls._put_data,
        #     'event_teams/{}/{}/status'.format(event_key, team_key),
        #     status_json,
        #     _queue="firebase")
    """

    @classmethod
    def update_live_event(cls, event: Event) -> None:
        events_by_key: Dict[EventKey, Dict] = {
            event.key_name: cls._convert_event(event),
        }

        defer_safe(
            cls._put_data,
            "live_events",
            events_by_key,
            _queue="firebase",
            _target="py3-tasks-io",
            _url=f"/_ah/queue/deferred_firebase_update_live_events:{event.key_name}",
        )

    @classmethod
    def _convert_event(cls, event: Event) -> Dict:
        converted_event = EventConverter.eventConverter_v3(event)
        # Only what's needed to render webcast
        partial_event = {
            key: converted_event[key]
            for key in ["key", "name", "short_name", "webcasts"]
        }
        # Hack in district code
        if (district_key := event.district_key) and partial_event.get("short_name"):
            partial_event["short_name"] = "[{}] {}".format(
                none_throws(district_key.string_id())[4:].upper(),
                partial_event["short_name"],
            )

        return partial_event

    @classmethod
    def update_live_events(
        cls, events: Dict[EventKey, Event], special_webcasts: List[TSpecialWebcast]
    ) -> None:
        """
        Updates live_events and special webcasts
        """
        events_by_key: Dict[EventKey, Dict] = {}
        for event_key, event in events.items():
            partial_event = cls._convert_event(event)
            events_by_key[event_key] = partial_event

        defer_safe(
            cls._put_data,
            "live_events",
            events_by_key,
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_live_events",
        )

        defer_safe(
            cls._put_data,
            "special_webcasts",
            special_webcasts,
            _queue="firebase",
            _target="py3-tasks-io",
            _url="/_ah/queue/deferred_firebase_update_special_webcasts",
        )

    @classmethod
    def update_event_queue_status(
        cls, event: Event, queue_status: EventQueueStatus
    ) -> None:
        if now_queuing := queue_status.get("now_queueing"):
            update_data = {
                "now_queuing": {
                    "name": now_queuing["match_name"],
                    "key": now_queuing["match_key"],
                }
            }
            defer_safe(
                cls._patch_data,
                f"live_events/{event.key_name}",
                update_data,
                _queue="firebase",
                _target="py3-tasks-io",
                _url=f"/_ah/queue/deferred_firebase_update_event_queue_status:{event.key_name}",
            )
        else:
            defer_safe(
                cls._delete_data,
                f"live_events/{event.key_name}/now_queuing",
                _queue="firebase",
                _target="py3-tasks-io",
                _url=f"/_ah/queue/deferred_firebase_update_event_queue_status:{event.key_name}",
            )

    """
    @classmethod
    def update_event(cls, event: Event) -> None:
        WebcastOnlineHelper.add_online_status(event.webcast)

        converted_event = EventConverter.eventConverter_v3(event)
        defer_safe(
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
