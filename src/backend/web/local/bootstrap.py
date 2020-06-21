import datetime
import json
from typing import Dict, Optional

import requests
from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


class LocalDataBootstrap:
    EVENT_DATE_FORMAT_STR = "%Y-%m-%d"
    AUTH_HEADER = "X-TBA-Auth-Key"

    """
    def store_district(data):
        district = District(id=data['key'])
        district.year = data['year']
        district.abbreviation = data['abbreviation']
        district.display_name = data['display_name']

        return DistrictManipulator.createOrUpdate(district)
    """

    @classmethod
    def store_event(cls, data: Dict) -> Event:
        event = Event(id=data["key"])
        event.name = data["name"]
        event.short_name = data["short_name"]
        event.event_short = data["event_code"]
        event.event_type_enum = data["event_type"]
        event.year = data["year"]
        event.timezone_id = data["timezone"]
        event.website = data["website"]
        event.start_date = (
            datetime.datetime.strptime(data["start_date"], cls.EVENT_DATE_FORMAT_STR)
            if data["start_date"]
            else None
        )
        event.end_date = (
            datetime.datetime.strptime(data["end_date"], cls.EVENT_DATE_FORMAT_STR)
            if data["end_date"]
            else None
        )
        event.webcast_json = json.dumps(data["webcasts"])
        event.venue = data["location_name"]
        event.city = data["city"]
        event.state_prov = data["state_prov"]
        event.country = data["country"]
        event.playoff_type = data["playoff_type"]
        event.parent_event = (
            ndb.Key(Event, data["parent_event_key"])
            if data["parent_event_key"]
            else None
        )
        event.divisions = (
            [ndb.Key(Event, div_key) for div_key in data["division_keys"]]
            if data["division_keys"]
            else []
        )

        # district = store_district(data['district']) if data['district'] else None
        # event.district_key = district.key if district else None

        # return EventManipulator.createOrUpdate(event)
        event.put()
        return event

    @staticmethod
    def store_team(data: Dict) -> Team:
        team = Team(id=data["key"])
        team.team_number = data["team_number"]
        team.nickname = data["nickname"]
        team.name = data["name"]
        team.website = data["website"]
        team.rookie_year = data["rookie_year"]
        team.motto = data["motto"]
        team.city = data["city"]
        team.state_prov = data["state_prov"]
        team.country = data["country"]
        team.school_name = data["school_name"]

        # TeamManipulator.createOrUpdate(team)
        team.put()
        return team

    """
    def store_match(data):
        match = Match(id=data['key'])
        match.event = ndb.Key(Event, data['event_key'])
        match.year = int(data['key'][:4])
        match.comp_level = data['comp_level']
        match.set_number = data['set_number']
        match.match_number = data['match_number']
        if data.get('time'):
            match.time = datetime.datetime.fromtimestamp(int(data['time']))

        if data.get('actual_time'):
            match.actual_time = datetime.datetime.fromtimestamp(int(data['actual_time']))

        if data.get('predicted_time'):
            match.predicted_time = datetime.datetime.fromtimestamp(int(data['predicted_time']))

        if data.get('post_result_time'):
            match.post_result_time = datetime.datetime.fromtimestamp(int(data['post_result_time']))
        match.score_breakdown_json = json.dumps(data['score_breakdown'])

        team_key_names = []
        for alliance in ['red', 'blue']:
            team_key_names += data['alliances'][alliance]['team_keys']
            data['alliances'][alliance]['teams'] = data['alliances'][alliance].pop('team_keys')
            data['alliances'][alliance]['surrogates'] = data['alliances'][alliance].pop('surrogate_team_keys')
            data['alliances'][alliance]['dqs'] = data['alliances'][alliance].pop('dq_team_keys')
        match.alliances_json = json.dumps(data['alliances'])
        match.team_key_names = team_key_names

        youtube_videos = []
        for video in data['videos']:
            if video['type'] == 'youtube':
                youtube_videos.append(video['key'])
        match.youtube_videos = youtube_videos

        return MatchManipulator.createOrUpdate(match)
    """

    @staticmethod
    def store_eventteam(team: Team, event: Event) -> EventTeam:
        eventteam = EventTeam(id="{}_{}".format(event.key_name, team.key_name))
        eventteam.event = event.key
        eventteam.team = team.key
        eventteam.year = event.year

        # return EventTeamManipulator.createOrUpdate(eventteam)
        eventteam.put()
        return eventteam

    """
    def store_eventdetail(event, type, data):
        detail = EventDetails(id=event.key_name)
        setattr(detail, type, data)

        return EventDetailsManipulator.createOrUpdate(detail)
    """

    """"
    def store_award(data, event):
        award = Award(id=Award.render_key_name(data['event_key'], data['award_type']))
        award.event = ndb.Key(Event, data['event_key'])
        award.award_type_enum = data['award_type']
        award.year = data['year']
        award.name_str = data['name']
        award.event_type_enum = event.event_type_enum

        recipient_list_fixed = []
        team_keys = []
        for recipient in data['recipient_list']:
            if recipient['team_key']:
                team_keys.append(ndb.Key(Team, recipient['team_key']))
            recipient_list_fixed.append(json.dumps({
                'awardee': recipient['awardee'],
                'team_number': recipient['team_key'][3:] if recipient['team_key'] else None,
            }))
        award.recipient_json_list = recipient_list_fixed
        return AwardManipulator.createOrUpdate(award)
    """

    @classmethod
    def fetch_endpoint(cls, endpoint: str, auth_token: str) -> Dict:
        full_url = f"https://www.thebluealliance.com/api/v3/{endpoint}"
        r = requests.get(
            full_url, headers={cls.AUTH_HEADER: auth_token, "User-agent": "Mozilla/5.0"}
        )
        return r.json()

    @classmethod
    def fetch_team(cls, team_key: str, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"team/{team_key}", auth_token)

    @classmethod
    def fetch_event(cls, event_key: str, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"event/{event_key}", auth_token)

    """
    def fetch_match(match_key):
        return fetch_endpoint("match/{}".format(match_key))
    """

    @classmethod
    def fetch_event_detail(cls, event_key: str, detail: str, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"event/{event_key}/{detail}", auth_token)

    @classmethod
    def update_event(cls, key: str, auth_token: str) -> None:
        event_data = cls.fetch_event(key, auth_token)
        event = cls.store_event(event_data)

        event_teams = cls.fetch_event_detail(key, "teams", auth_token)
        teams = list(map(cls.store_team, event_teams))
        list(map(lambda t: cls.store_eventteam(t, event), teams))

        """
        event_matches = fetch_event_detail(key, 'matches')
        map(store_match, event_matches)

        event_rankings = fetch_event_detail(key, 'rankings')
        store_eventdetail(event, 'rankings2', event_rankings['rankings'] if event_rankings else [])

        event_alliances = fetch_event_detail(key, 'alliances')
        store_eventdetail(event, 'alliance_selections', event_alliances)

        event_awards = fetch_event_detail(key, 'awards')
        map(lambda t: store_award(t, event), event_awards)
        """

    @classmethod
    def bootstrap_key(cls, key: str, apiv3_key: str) -> Optional[str]:
        """
        if Match.validate_key_name(key):
            match_data = fetch_match(key)
            store_match(match_data)
        """

        if Event.validate_key_name(key):
            cls.update_event(key, apiv3_key)
            return f"/event/{key}"
        elif Team.validate_key_name(key):
            team_data = cls.fetch_team(key, apiv3_key)
            cls.store_team(team_data)
            return f"/team/{key[3:]}"
        elif key.isdigit():
            event_keys = [
                event["key"] for event in cls.fetch_endpoint(f"events/{key}", apiv3_key)
            ]
            for event in event_keys:
                cls.update_event(event, apiv3_key)
            return f"/events/{key}"
        else:
            return None
