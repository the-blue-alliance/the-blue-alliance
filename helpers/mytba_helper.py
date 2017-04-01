from collections import defaultdict

import datetime
from google.appengine.ext import ndb

from consts.model_type import ModelType
from database.award_query import TeamYearAwardsQuery
from database.event_query import TeamYearEventsQuery
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.notification_helper import NotificationHelper
from models.account import Account
from models.event_team import EventTeam
from models.favorite import Favorite
from models.subscription import Subscription
from models.team import Team


class MyTBAHelper(object):
    @classmethod
    def add_favorite(cls, fav, device_key=""):
        if Favorite.query(Favorite.model_key == fav.model_key, Favorite.model_type == fav.model_type,
                          ancestor=ndb.Key(Account, fav.user_id)).count() == 0:
            # Favorite doesn't exist, add it
            fav.put()
            # Send updates to user's other devices
            NotificationHelper.send_favorite_update(fav.user_id, device_key)
            return 200
        else:
            # Favorite already exists. Don't add it again
            return 304

    @classmethod
    def remove_favorite(cls, user_id, model_key, model_type, device_key=""):
        to_delete = Favorite.query(Favorite.model_key == model_key, Favorite.model_type == model_type,
                                   ancestor=ndb.Key(Account, user_id)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            NotificationHelper.send_favorite_update(user_id, device_key)
            return 200
        else:
            # Favorite doesn't exist. Can't delete it
            return 404

    @classmethod
    def add_subscription(cls, sub, device_key=""):
        current = Subscription.query(Subscription.model_key == sub.model_key, Subscription.model_type == sub.model_type,
                                     ancestor=ndb.Key(Account, sub.user_id)).get()
        if current is None:
            # Subscription doesn't exist, add it
            sub.put()
            # Send updates to user's other devices
            NotificationHelper.send_subscription_update(sub.user_id, device_key)
            return 200
        else:
            if len(set(current.notification_types).symmetric_difference(set(sub.notification_types))) == 0:
                # Subscription already exists. Don't add it again
                return 304
            else:
                # We're updating the settings
                current.notification_types = sub.notification_types
                current.put()
                # Send updates to user's other devices
                NotificationHelper.send_subscription_update(sub.user_id, device_key)
                return 200

    @classmethod
    def remove_subscription(cls, user_id, model_key, model_type, device_key=""):
        to_delete = Subscription.query(Subscription.model_key == model_key, Subscription.model_type == model_type,
                                       ancestor=ndb.Key(Account, user_id)).fetch(keys_only=True)
        if len(to_delete) > 0:
            ndb.delete_multi(to_delete)
            # Send updates to user's other devices
            NotificationHelper.send_subscription_update(user_id, device_key)
            return 200
        else:
            # Subscription doesn't exist. Can't delete it
            return 404

    @classmethod
    def render_favorite_teams_events(cls, favorite_teams, favorite_teams_events_futures, favorite_teams_awards_futures):
        past_events_by_event = {}
        live_events_by_event = {}
        future_events_by_event = {}
        favorite_event_team_keys = []
        for team, events_future in zip(favorite_teams, favorite_teams_events_futures):
            events = events_future.get_result()
            if not events:
                continue
            EventHelper.sort_events(events)  # Sort by date
            for event in events:
                favorite_event_team_keys.append(ndb.Key(EventTeam, '{}_{}'.format(event.key.id(), team.key.id())))
                if event.within_a_day:
                    if event.key_name not in live_events_by_event:
                        live_events_by_event[event.key_name] = (event, [])
                    live_events_by_event[event.key_name][1].append(team)
                elif event.start_date < datetime.datetime.now():
                    if event.key_name not in past_events_by_event:
                        past_events_by_event[event.key_name] = (event, [])
                    past_events_by_event[event.key_name][1].append(team)
                else:
                    if event.key_name not in future_events_by_event:
                        future_events_by_event[event.key_name] = (event, [])
                    future_events_by_event[event.key_name][1].append(team)

        event_team_awards = defaultdict(lambda: defaultdict(list))
        for team_key, awards_future in favorite_teams_awards_futures.items():
            for award in awards_future.get_result():
                event_team_awards[award.event.id()][team_key].append(award)
        return past_events_by_event, live_events_by_event, future_events_by_event, favorite_event_team_keys, event_team_awards

    @classmethod
    def render_live_events_with_teams(cls, live_events_by_event):
        live_events_with_teams = []
        for event, teams in live_events_by_event.itervalues():
            teams_and_statuses = []
            for team in teams:
                event_team = EventTeam.get_by_id('{}_{}'.format(event.key.id(), team.key.id()))  # Should be in context cache
                status_str = {
                    'alliance': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team.key.id(), event_team.status),
                    'playoff': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team.key.id(), event_team.status),
                }
                teams_and_statuses.append((
                    team,
                    event_team.status,
                    status_str
                ))
            teams_and_statuses.sort(key=lambda x: x[0].team_number)
            live_events_with_teams.append((event, teams_and_statuses))
        live_events_with_teams.sort(key=lambda x: x[0].name)
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))
        return live_events_with_teams

    @classmethod
    def build_live_favorite_futures(cls, user, year):
        team_favorites_future = Favorite.query(Favorite.model_type == ModelType.TEAM, ancestor=user).fetch_async()

        favorite_team_keys = map(lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result())
        favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

        favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

        favorite_teams_events_futures = []
        favorite_teams_awards_futures = {}
        for team in favorite_teams:
            favorite_teams_events_futures.append(TeamYearEventsQuery(team.key_name, year).fetch_async())
            favorite_teams_awards_futures[team.key.id()] = TeamYearAwardsQuery(team.key_name, year).fetch_async()
        return favorite_teams, favorite_teams_events_futures, favorite_teams_awards_futures
