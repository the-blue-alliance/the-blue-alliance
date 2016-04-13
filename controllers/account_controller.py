import os
import logging
import datetime

from collections import defaultdict

from google.appengine.ext import ndb

from base_controller import LoggedInHandler

from consts.account_permissions import AccountPermissions
from consts.client_type import ClientType
from consts.model_type import ModelType
from consts.notification_type import NotificationType

from helpers.event_helper import EventHelper
from helpers.mytba_helper import MyTBAHelper
from helpers.notification_helper import NotificationHelper
from helpers.validation_helper import ValidationHelper

from models.account import Account
from models.event import Event
from models.favorite import Favorite
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.suggestion import Suggestion
from models.team import Team

from template_engine import jinja2_engine

import tba_config


class AccountOverview(LoggedInHandler):
    def get(self):
        redirect = self.request.get('redirect')
        if redirect:
            self._require_login(redirect)
        else:
            self._require_login('/account')
        # Redirects to registration page if account not registered
        self._require_registration('/account/register')

        push_sitevar = Sitevar.get_by_id('notifications.enable')
        if push_sitevar is None or not push_sitevar.values_json == "true":
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
        if AccountPermissions.MUTATE_DATA in self.user_bundle.account.permissions:
            review_permissions = True
            num_reviewed = Suggestion.query(Suggestion.reviewer==user).count()
            total_pending = Suggestion.query(Suggestion.review_state==Suggestion.REVIEW_PENDING).count()

        self.template_values['status'] = self.request.get('status')
        self.template_values['webhook_verification_success'] = self.request.get('webhook_verification_success')
        self.template_values['ping_enabled'] = ping_enabled
        self.template_values['num_favorites'] = num_favorites
        self.template_values['num_subscriptions'] = num_subscriptions
        self.template_values['submissions_pending'] = submissions_pending
        self.template_values['submissions_accepted'] = submissions_accepted
        self.template_values['review_permissions'] = review_permissions
        self.template_values['num_reviewed'] = num_reviewed
        self.template_values['total_pending'] = total_pending

        self.response.out.write(jinja2_engine.render('account_overview.html', self.template_values))


class AccountEdit(LoggedInHandler):
    def get(self):
        self._require_login('/account/edit')
        self._require_registration('/account/register')

        self.response.out.write(jinja2_engine.render('account_edit.html', self.template_values))

    def post(self):
        self._require_login('/account/edit')
        self._require_registration('/account/register')

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
        self._require_login('/account/register')
        # Redirects to account overview page if already registered
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        self.response.out.write(jinja2_engine.render('account_register.html', self.template_values))

    def post(self):
        self._require_login('/account/register')
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            account = Account.get_by_id(self.user_bundle.account.key.id())
            account.display_name = self.request.get('display_name')
            account.registered = True
            account.put()
            self.redirect('/account')
        else:
            self.redirect('/')


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


class MyTBAController(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

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
        for item in favorites + subscriptions:
            if item.model_type == ModelType.TEAM:
                team_keys.add(ndb.Key(Team, item.model_key))
                if type(item) == Favorite:
                    team_fav[item.model_key] = item
                elif type(item) == Subscription:
                    team_subs[item.model_key] = item
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

        self.template_values['team_fav_subs'] = team_fav_subs
        self.template_values['event_fav_subs'] = event_fav_subs
        self.template_values['status'] = self.request.get('status')
        self.template_values['year'] = datetime.datetime.now().year

        self.response.out.write(jinja2_engine.render('mytba.html', self.template_values))


class MyTBAEventController(LoggedInHandler):
    def get(self, event_key):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        # Handle wildcard for all events in a year
        event = None
        is_wildcard = False
        if event_key.endswith('*'):
            try:
                year = int(event_key[:-1])
            except:
                year = None
            if year and year >= 1992 and year <= tba_config.MAX_YEAR:
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
        self._require_login('/account/register')
        self._require_registration('/account/register')

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


class MyTBATeamController(LoggedInHandler):
    def get(self, team_number):
        self._require_login('/account/register')
        self._require_registration('/account/register')

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
        self._require_login('/account/register')
        self._require_registration('/account/register')

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
