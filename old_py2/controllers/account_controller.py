import os
import logging
import datetime
import random
import string

from collections import defaultdict

from google.appengine.ext import ndb

from base_controller import LoggedInHandler

from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from consts.client_type import ClientType
from consts.model_type import ModelType
from consts.notification_type import NotificationType

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.mytba_helper import MyTBAHelper
from helpers.notification_helper import NotificationHelper
from helpers.validation_helper import ValidationHelper

from models.account import Account
from models.api_auth_access import ApiAuthAccess
from models.event import Event
from models.favorite import Favorite
from models.match import Match
from models.subscription import Subscription
from models.suggestion import Suggestion
from models.team import Team

from sitevars.notifications_enable import NotificationsEnable

from template_engine import jinja2_engine

import tba_config


class AccountOverview(LoggedInHandler):
    def get(self):
        self._require_registration()

        notifications_enabled = NotificationsEnable.notifications_enabled()
        if not notifications_enabled:
            ping_enabled = "disabled"
        else:
            ping_enabled = ""

        # Compute myTBA statistics
        user = self.user_bundle.account.key
        num_favorites = Favorite.query(ancestor=user).count()
        num_subscriptions = Subscription.query(ancestor=user).count()

        # Compute suggestion statistics
        submissions_pending = Suggestion.query(Suggestion.review_state==Suggestion.REVIEW_PENDING, Suggestion.author==user).count()
        submissions_accepted = Suggestion.query(Suggestion.review_state==Suggestion.REVIEW_ACCEPTED, Suggestion.author==user).count()

        # Suggestion review statistics
        review_permissions = False
        num_reviewed = 0
        total_pending = 0
        if self.user_bundle.account.permissions:
            review_permissions = True
            num_reviewed = Suggestion.query(Suggestion.reviewer==user).count()
            total_pending = Suggestion.query(Suggestion.review_state==Suggestion.REVIEW_PENDING).count()

        # Fetch trusted API keys
        api_keys = ApiAuthAccess.query(ApiAuthAccess.owner == user).fetch()
        write_keys = filter(lambda key: key.is_write_key, api_keys)
        write_keys.sort(key=lambda key: key.event_list[0])
        read_keys = filter(lambda key: key.is_read_key, api_keys)

        self.template_values['status'] = self.request.get('status')
        self.template_values['webhook_verification_success'] = self.request.get('webhook_verification_success')
        self.template_values['ping_sent'] = self.request.get('ping_sent')
        self.template_values['ping_enabled'] = ping_enabled
        self.template_values['num_favorites'] = num_favorites
        self.template_values['num_subscriptions'] = num_subscriptions
        self.template_values['submissions_pending'] = submissions_pending
        self.template_values['submissions_accepted'] = submissions_accepted
        self.template_values['review_permissions'] = review_permissions
        self.template_values['num_reviewed'] = num_reviewed
        self.template_values['total_pending'] = total_pending
        self.template_values['read_keys'] = read_keys
        self.template_values['write_keys'] = write_keys
        self.template_values['auth_write_type_names'] = AuthType.write_type_names

        self.response.out.write(jinja2_engine.render('account_overview.html', self.template_values))


class AccountEdit(LoggedInHandler):
    def get(self):
        self._require_registration()

        self.response.out.write(jinja2_engine.render('account_edit.html', self.template_values))

    def post(self):
        self._require_registration()

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            user = Account.get_by_id(self.user_bundle.account.key.id())
            user.display_name = self.request.get('display_name')
            user.put()
            self.redirect('/account?status=account_edit_success')
        else:
            self.redirect('/account?status=account_edit_failure')


class AccountRegister(LoggedInHandler):
    def get(self):
        self._require_login()

        # Redirects if already registered
        redirect = self.request.get('redirect')
        if self.user_bundle.account.registered:
            if redirect:
                self.redirect(redirect, abort=True)
            else:
                self.redirect('/account', abort=True)

        self.template_values['redirect'] = redirect
        self.template_values['logout_url'] = self.user_bundle.create_logout_url(redirect)
        self.response.out.write(jinja2_engine.render('account_register.html', self.template_values))

    def post(self):
        self._require_login()
        if self.user_bundle.account.registered:
            self.redirect('/account', abort=True)

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            account = Account.get_by_id(self.user_bundle.account.key.id())
            account.display_name = self.request.get('display_name')
            account.registered = True
            account.put()

            redirect = self.request.get('redirect')
            if redirect:
                self.redirect(redirect, abort=True)
            else:
                self.redirect('/account', abort=True)
        else:
            self.redirect('/')


class AccountLogin(LoggedInHandler):
    def get(self):
        if self.user_bundle.user:
            self.redirect('/account', abort=True)

        redirect = self.request.get('redirect')
        if redirect:
            url = self._get_login_url(redirect)
        else:
            url = self._get_login_url('/account')
        self.redirect(url, abort=True)


class AccountLoginRequired(LoggedInHandler):
    def get(self):
        self.template_values['redirect'] = self.request.get('redirect')
        self.response.out.write(jinja2_engine.render('account_login_required.html', self.template_values))


class AccountLogout(LoggedInHandler):
    def get(self):
        if os.environ.get('SERVER_SOFTWARE', '').startswith('Development/'):
            self.redirect(self.user_bundle.logout_url)
            return

        # Deletes the session cookies pertinent to TBA without touching Google session(s)
        # Reference: http://ptspts.blogspot.ca/2011/12/how-to-log-out-from-appengine-app-only.html
        response = self.redirect('/')
        response.delete_cookie('ACSID')
        response.delete_cookie('SACSID')

        return response


class AccountAPIReadKeyAdd(LoggedInHandler):
    def post(self):
        self._require_registration()

        description = self.request.get('description')
        if description:
            ApiAuthAccess(
                id=''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(64)),
                owner=self.user_bundle.account.key,
                auth_types_enum=[AuthType.READ_API],
                description=description,
            ).put()
            self.redirect('/account?status=read_key_add_success')
        else:
            self.redirect('/account?status=read_key_add_no_description')


class AccountAPIReadKeyDelete(LoggedInHandler):
    def post(self):
        self._require_registration()

        key_id = self.request.get('key_id')
        auth = ApiAuthAccess.get_by_id(key_id)

        if auth and auth.owner == self.user_bundle.account.key:
            auth.key.delete()
            self.redirect('/account?status=read_key_delete_success')
        else:
            self.redirect('/account?status=read_key_delete_failure')


class MyTBAController(LoggedInHandler):
    def get(self):
        self._require_registration()

        user = self.user_bundle.account.key
        favorites = Favorite.query(ancestor=user).fetch()
        subscriptions = Subscription.query(ancestor=user).fetch()

        team_keys = set()
        team_fav = {}
        team_subs = {}
        event_keys = set()
        event_fav = {}
        event_subs = {}
        events = []
        match_keys = set()
        match_event_keys = set()
        match_fav = {}
        match_subs = {}
        for item in favorites + subscriptions:
            if item.model_type == ModelType.TEAM:
                team_keys.add(ndb.Key(Team, item.model_key))
                if type(item) == Favorite:
                    team_fav[item.model_key] = item
                elif type(item) == Subscription:
                    team_subs[item.model_key] = item
            elif item.model_type == ModelType.MATCH:
                match_keys.add(ndb.Key(Match, item.model_key))
                match_event_keys.add(ndb.Key(Event, item.model_key.split('_')[0]))
                if type(item) == Favorite:
                    match_fav[item.model_key] = item
                elif type(item) == Subscription:
                    match_subs[item.model_key] = item
            elif item.model_type == ModelType.EVENT:
                if item.model_key.endswith('*'):  # All year events wildcard
                    event_year = int(item.model_key[:-1])
                    events.append(Event(  # add fake event for rendering
                        id=item.model_key,
                        short_name='ALL EVENTS',
                        event_short=item.model_key,
                        year=event_year,
                        start_date=datetime.datetime(event_year, 1, 1),
                        end_date=datetime.datetime(event_year, 1, 1)
                    ))
                else:
                    event_keys.add(ndb.Key(Event, item.model_key))
                if type(item) == Favorite:
                    event_fav[item.model_key] = item
                elif type(item) == Subscription:
                    event_subs[item.model_key] = item

        team_futures = ndb.get_multi_async(team_keys)
        event_futures = ndb.get_multi_async(event_keys)
        match_futures = ndb.get_multi_async(match_keys)
        match_event_futures = ndb.get_multi_async(match_event_keys)

        teams = sorted([team_future.get_result() for team_future in team_futures], key=lambda x: x.team_number)
        team_fav_subs = []
        for team in teams:
            fav = team_fav.get(team.key.id(), None)
            subs = team_subs.get(team.key.id(), None)
            team_fav_subs.append((team, fav, subs))

        events += [event_future.get_result() for event_future in event_futures]
        EventHelper.sort_events(events)

        event_fav_subs = []
        for event in events:
            fav = event_fav.get(event.key.id(), None)
            subs = event_subs.get(event.key.id(), None)
            event_fav_subs.append((event, fav, subs))

        matches = [match_future.get_result() for match_future in match_futures]
        match_events = [match_event_future.get_result() for match_event_future in match_event_futures]
        MatchHelper.natural_sort_matches(matches)

        match_fav_subs_by_event = {}
        for event in match_events:
            match_fav_subs_by_event[event.key.id()] = (event, [])

        for match in matches:
            event_key = match.key.id().split('_')[0]
            fav = match_fav.get(match.key.id(), None)
            subs = match_subs.get(match.key.id(), None)
            match_fav_subs_by_event[event_key][1].append((match, fav, subs))

        event_match_fav_subs = sorted(match_fav_subs_by_event.values(), key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        event_match_fav_subs = sorted(event_match_fav_subs, key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        self.template_values['team_fav_subs'] = team_fav_subs
        self.template_values['event_fav_subs'] = event_fav_subs
        self.template_values['event_match_fav_subs'] = event_match_fav_subs
        self.template_values['status'] = self.request.get('status')
        self.template_values['year'] = datetime.datetime.now().year

        self.response.out.write(jinja2_engine.render('mytba.html', self.template_values))


class myTBAAddHotMatchesController(LoggedInHandler):
    def get(self, event_key=None):
        self._require_registration()

        if event_key is None:
            events = EventHelper.getEventsWithinADay()
            EventHelper.sort_events(events)
            self.template_values['events'] = events
            self.response.out.write(jinja2_engine.render('mytba_add_hot_matches_base.html', self.template_values))
            return

        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        subscriptions_future = Subscription.query(
            Subscription.model_type==ModelType.MATCH,
            Subscription.notification_types==NotificationType.UPCOMING_MATCH,
            ancestor=self.user_bundle.account.key).fetch_async(projection=[Subscription.model_key])

        matches = []
        if event.details and event.details.predictions and event.details.predictions['match_predictions']:
            match_predictions = dict(
                event.details.predictions['match_predictions']['qual'].items() +
                event.details.predictions['match_predictions']['playoff'].items())
            max_hotness = 0
            min_hotness = float('inf')
            for match in event.matches:
                if not match.has_been_played and match.key.id() in match_predictions:
                    prediction = match_predictions[match.key.id()]
                    red_score = prediction['red']['score']
                    blue_score = prediction['blue']['score']
                    if red_score > blue_score:
                        winner_score = red_score
                        loser_score = blue_score
                    else:
                        winner_score = blue_score
                        loser_score = red_score

                    hotness = winner_score + 2.0*loser_score  # Favor close high scoring matches

                    max_hotness = max(max_hotness, hotness)
                    min_hotness = min(min_hotness, hotness)
                    match.hotness = hotness
                    matches.append(match)

        existing_subscriptions = set()
        for sub in subscriptions_future.get_result():
            existing_subscriptions.add(sub.model_key)

        hot_matches = []
        for match in matches:
            match.hotness = 100 * (match.hotness - min_hotness) / (max_hotness - min_hotness)
            match.already_subscribed = match.key.id() in existing_subscriptions
            hot_matches.append(match)
        hot_matches = sorted(hot_matches, key=lambda match: -match.hotness)
        matches_dict = {'qm': hot_matches[:25]}

        self.template_values['event'] = event
        self.template_values['matches'] = matches_dict

        self.response.out.write(jinja2_engine.render('mytba_add_hot_matches.html', self.template_values))

    def post(self, event_key):
        self._require_registration()

        current_user_id = self.user_bundle.account.key.id()

        event = Event.get_by_id(event_key)
        subscribed_matches = set(self.request.get_all('subscribed_matches'))

        for match in event.matches:
            if not match.has_been_played:
                match_key = match.key.id()
                if match.key.id() in subscribed_matches:
                    sub = Subscription(
                        parent=ndb.Key(Account, current_user_id),
                        user_id=current_user_id,
                        model_type=ModelType.MATCH,
                        model_key=match_key,
                        notification_types=[NotificationType.UPCOMING_MATCH]
                    )
                    MyTBAHelper.add_subscription(sub)
                else:
                    MyTBAHelper.remove_subscription(current_user_id, match_key, ModelType.MATCH)

        self.redirect('/account/mytba?status=match_updated#my-matches'.format(event_key))


class MyTBAEventController(LoggedInHandler):
    def get(self, event_key):
        self._require_registration()

        # Handle wildcard for all events in a year
        event = None
        is_wildcard = False
        if event_key.endswith('*'):
            try:
                year = int(event_key[:-1])
            except:
                year = None
            if year and year in tba_config.VALID_YEARS:
                event = Event(  # fake event for rendering
                    name="ALL {} EVENTS".format(year),
                    year=year,
                )
                is_wildcard = True
        else:
            event = Event.get_by_id(event_key)

        if not event:
            self.abort(404)

        user = self.user_bundle.account.key
        favorite = Favorite.query(Favorite.model_key==event_key, Favorite.model_type==ModelType.EVENT, ancestor=user).get()
        subscription = Subscription.query(Favorite.model_key==event_key, Favorite.model_type==ModelType.EVENT, ancestor=user).get()

        if not favorite and not subscription:  # New entry; default to being a favorite
            is_favorite = True
        else:
            is_favorite = favorite is not None

        enabled_notifications = [(en, NotificationType.render_names[en]) for en in NotificationType.enabled_event_notifications]

        self.template_values['event'] = event
        self.template_values['is_wildcard'] = is_wildcard
        self.template_values['is_favorite'] = is_favorite
        self.template_values['subscription'] = subscription
        self.template_values['enabled_notifications'] = enabled_notifications

        self.response.out.write(jinja2_engine.render('mytba_event.html', self.template_values))

    def post(self, event_key):
        self._require_registration()

        current_user_id = self.user_bundle.account.key.id()

        if self.request.get('favorite'):
            favorite = Favorite(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.EVENT,
                model_key=event_key
            )
            MyTBAHelper.add_favorite(favorite)
        else:
            MyTBAHelper.remove_favorite(current_user_id, event_key, ModelType.EVENT)

        subs = self.request.get_all('notification_types')
        if subs:
            subscription = Subscription(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.EVENT,
                model_key=event_key,
                notification_types=[int(s) for s in subs]
            )
            MyTBAHelper.add_subscription(subscription)
        else:
            MyTBAHelper.remove_subscription(current_user_id, event_key, ModelType.EVENT)

        self.redirect('/account/mytba?status=event_updated#my-events')


class MyTBAMatchController(LoggedInHandler):
    def get(self, match_key):
        self._require_registration()

        match = Match.get_by_id(match_key)

        if not match:
            self.abort(404)

        user = self.user_bundle.account.key
        favorite = Favorite.query(Favorite.model_key==match_key, Favorite.model_type==ModelType.MATCH, ancestor=user).get()
        subscription = Subscription.query(Favorite.model_key==match_key, Favorite.model_type==ModelType.MATCH, ancestor=user).get()

        if not favorite and not subscription:  # New entry; default to being a favorite
            is_favorite = True
        else:
            is_favorite = favorite is not None

        enabled_notifications = [(en, NotificationType.render_names[en]) for en in NotificationType.enabled_match_notifications]

        self.template_values['match'] = match
        self.template_values['is_favorite'] = is_favorite
        self.template_values['subscription'] = subscription
        self.template_values['enabled_notifications'] = enabled_notifications

        self.response.out.write(jinja2_engine.render('mytba_match.html', self.template_values))

    def post(self, match_key):
        self._require_registration()

        current_user_id = self.user_bundle.account.key.id()
        match = Match.get_by_id(match_key)

        if self.request.get('favorite'):
            favorite = Favorite(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.MATCH,
                model_key=match_key
            )
            MyTBAHelper.add_favorite(favorite)
        else:
            MyTBAHelper.remove_favorite(current_user_id, match_key, ModelType.MATCH)

        subs = self.request.get_all('notification_types')
        if subs:
            subscription = Subscription(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.MATCH,
                model_key=match_key,
                notification_types=[int(s) for s in subs]
            )
            MyTBAHelper.add_subscription(subscription)
        else:
            MyTBAHelper.remove_subscription(current_user_id, match_key, ModelType.MATCH)

        self.redirect('/account/mytba?status=match_updated#my-matches')


class MyTBATeamController(LoggedInHandler):
    def get(self, team_number):
        self._require_registration()

        team_key = 'frc{}'.format(team_number)
        team = Team.get_by_id(team_key)

        if not team:
            self.abort(404)

        user = self.user_bundle.account.key
        favorite = Favorite.query(Favorite.model_key==team_key, Favorite.model_type==ModelType.TEAM, ancestor=user).get()
        subscription = Subscription.query(Favorite.model_key==team_key, Favorite.model_type==ModelType.TEAM, ancestor=user).get()

        if not favorite and not subscription:  # New entry; default to being a favorite
            is_favorite = True
        else:
            is_favorite = favorite is not None

        enabled_notifications = [(en, NotificationType.render_names[en]) for en in NotificationType.enabled_team_notifications]

        self.template_values['team'] = team
        self.template_values['is_favorite'] = is_favorite
        self.template_values['subscription'] = subscription
        self.template_values['enabled_notifications'] = enabled_notifications

        self.response.out.write(jinja2_engine.render('mytba_team.html', self.template_values))

    def post(self, team_number):
        self._require_registration()

        current_user_id = self.user_bundle.account.key.id()
        team_key = 'frc{}'.format(team_number)

        if self.request.get('favorite'):
            favorite = Favorite(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.TEAM,
                model_key=team_key
            )
            MyTBAHelper.add_favorite(favorite)
        else:
            MyTBAHelper.remove_favorite(current_user_id, team_key, ModelType.TEAM)

        subs = self.request.get_all('notification_types')
        if subs:
            subscription = Subscription(
                parent=ndb.Key(Account, current_user_id),
                user_id=current_user_id,
                model_type=ModelType.TEAM,
                model_key=team_key,
                notification_types=[int(s) for s in subs]
            )
            MyTBAHelper.add_subscription(subscription)
        else:
            MyTBAHelper.remove_subscription(current_user_id, team_key, ModelType.TEAM)

        self.redirect('/account/mytba?status=team_updated#my-teams')
