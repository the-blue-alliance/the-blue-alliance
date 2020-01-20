import getpass
import urllib2

import datetime
import argparse
import json

import datetime

import sys

try:
    import dev_appserver
    dev_appserver.fix_sys_path()
    sys.path.insert(1, 'lib')
except ImportError:
    print('Please make sure the App Engine SDK is in your PYTHONPATH.')
    raise

from google.appengine.ext import ndb
from google.appengine.ext.remote_api import remote_api_stub

from models.award import Award
from models.district import District
from models.event import Event
from models.event_team import EventTeam
from models.event_details import EventDetails
from models.match import Match
from models.team import Team

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.district_manipulator import DistrictManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.match_manipulator import MatchManipulator

EVENT_DATE_FORMAT_STR = '%Y-%m-%d'
BASE_URL = 'https://www.thebluealliance.com/api/v3/{}'
APP_HEADER = 'X-TBA-Auth-Key'
AUTH_TOKEN = ''


def store_district(data):
    district = District(id=data['key'])
    district.year = data['year']
    district.abbreviation = data['abbreviation']
    district.display_name = data['display_name']

    return DistrictManipulator.createOrUpdate(district)


def store_event(data):
    event = Event(id=data['key'])
    event.name = data['name']
    event.short_name = data['short_name']
    event.event_short = data['event_code']
    event.event_type_enum = data['event_type']
    event.year = data['year']
    event.timezone_id = data['timezone']
    event.website = data['website']
    event.start_date = datetime.datetime.strptime(data['start_date'], EVENT_DATE_FORMAT_STR) if data['start_date'] else None
    event.end_date = datetime.datetime.strptime(data['end_date'], EVENT_DATE_FORMAT_STR) if data['end_date'] else None
    event.webcast_json = json.dumps(data['webcasts'])
    event.venue = data['location_name']
    event.city = data['city']
    event.state_prov = data['state_prov']
    event.country = data['country']
    event.playoff_type = data['playoff_type']
    event.parent_event = ndb.Key(Event, data['parent_event_key']) if data['parent_event_key'] else None
    event.divisions = [ndb.Key(Event, div_key) for div_key in data['division_keys']] if data['division_keys'] else []

    district = store_district(data['district']) if data['district'] else None
    event.district_key = district.key if district else None

    return EventManipulator.createOrUpdate(event)


def store_team(data):
    team = Team(id=data['key'])
    team.team_number = data['team_number']
    team.nickname = data['nickname']
    team.name = data['name']
    team.website = data['website']
    team.rookie_year = data['rookie_year']
    team.motto = data['motto']
    team.city = data['city']
    team.state_prov = data['state_prov']
    team.country = data['country']
    team.school_name = data['school_name']

    TeamManipulator.createOrUpdate(team)
    return team


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


def store_eventteam(team, event):
    eventteam = EventTeam(id="{}_{}".format(event.key_name, team.key_name))
    eventteam.event = event.key
    eventteam.team = team.key
    eventteam.year = event.year

    return EventTeamManipulator.createOrUpdate(eventteam)


def store_eventdetail(event, type, data):
    detail = EventDetails(id=event.key_name)
    setattr(detail, type, data)

    return EventDetailsManipulator.createOrUpdate(detail)


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


def fetch_endpoint(endpoint):
    full_url = BASE_URL.format(endpoint)
    print "Fetching {}".format(full_url)
    url = urllib2.Request(full_url, headers={APP_HEADER: AUTH_TOKEN, 'User-agent': 'Mozilla/5.0'})
    response = urllib2.urlopen(url)
    return json.loads(response.read())


def fetch_team(team_key):
    return fetch_endpoint("team/{}".format(team_key))


def fetch_event(event_key):
    return fetch_endpoint("event/{}".format(event_key))


def fetch_match(match_key):
    return fetch_endpoint("match/{}".format(match_key))


def fetch_event_detail(event_key, detail):
    return fetch_endpoint("event/{}/{}".format(event_key, detail))


def local_auth_func():
    # Credentials don't matter on the local devserver
    return 'user', 'pass'


def update_event(key):
    event_data = fetch_event(key)
    event = store_event(event_data)

    event_teams = fetch_event_detail(key, 'teams')
    teams = map(store_team, event_teams)
    map(lambda t: store_eventteam(t, event), teams)

    event_matches = fetch_event_detail(key, 'matches')
    map(store_match, event_matches)

    event_rankings = fetch_event_detail(key, 'rankings')
    store_eventdetail(event, 'rankings2', event_rankings['rankings'] if event_rankings else [])

    event_alliances = fetch_event_detail(key, 'alliances')
    store_eventdetail(event, 'alliance_selections', event_alliances)

    event_awards = fetch_event_detail(key, 'awards')
    map(lambda t: store_award(t, event), event_awards)


def main(key, url):
    print "Configuring GAE Remote API on {} to import {}".format(url, key)
    if 'localhost' in url:
        remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', local_auth_func, url)
    else:
        remote_api_stub.ConfigureRemoteApiForOAuth(url, '/_ah/remote_api')

    print "Loading data from The Blue Alliance requires an API key"
    print "Please go to https://www.thebluealliance.com/account and generate a read API key"
    apiv3_key = raw_input("Enter your API key: ")

    global AUTH_TOKEN
    AUTH_TOKEN = apiv3_key

    if Match.validate_key_name(key):
        match_data = fetch_match(key)
        store_match(match_data)

    elif Event.validate_key_name(key):
        update_event(key)
    elif Team.validate_key_name(key):
        team_data = fetch_team(key)
        store_team(team_data)
    elif key.isdigit():
        event_keys = [event['key'] for event in fetch_endpoint('events/{}'.format(key))]
        for event in event_keys:
            update_event(event)
    else:
        print "Unknown key :("

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap a TBA Development Instance")
    parser.add_argument("key", help="Event, Team, or Match key to import")
    parser.add_argument("--url", help="App Engine Remote API URL", required=True)
    args = parser.parse_args()

    main(args.key, args.url)
