import os
import logging
import datetime

from collections import defaultdict

from google.appengine.ext import ndb

from base_controller import LoggedInHandler

from consts.client_type import ClientType
from consts.model_type import ModelType
from consts.notification_type import NotificationType

from helpers.mytba_helper import MyTBAHelper
from helpers.notification_helper import NotificationHelper
from helpers.validation_helper import ValidationHelper

from models.account import Account
from models.favorite import Favorite
from models.subscription import Subscription
from models.sitevar import Sitevar

from template_engine import jinja2_engine


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

        self.template_values['webhook_verification_success'] = self.request.get('webhook_verification_success')
        self.template_values['ping_enabled'] = ping_enabled

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
            self.redirect('/account')
        else:
            self.redirect('/')


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

        favorites_by_type = defaultdict(list)
        for fav in favorites:
            favorites_by_type[ModelType.type_names[fav.model_type]].append(fav)

        subscriptions_by_type = defaultdict(list)
        for sub in subscriptions:
            subscriptions_by_type[ModelType.type_names[sub.model_type]].append(sub)

        now = datetime.datetime.now()
        self.template_values['favorites_by_type'] = dict(favorites_by_type)
        self.template_values['subscriptions_by_type'] = dict(subscriptions_by_type)
        self.template_values['enabled_notifications'] = NotificationType.enabled_notifications
        self.template_values['this_year'] = now.year

        error = self.request.get('error')
        if error:
            if error == 'invalid_model':
                error_message = "Invalid model key"
            elif error == "no_sub_types":
                error_message = "No notification types selected"
            elif error == "invalid_account":
                error_message = "Invalid account"
            elif error == "invalid_year":
                error_message = "You can only subscribe to the current year"
            elif error == "sub_not_found":
                error_message = "Subscription not found"
            elif error == "fav_not_found":
                error_message = "Favorite not found"
            else:
                error_message = "An unknown error occurred"
            self.template_values['error_message'] = error_message

        self.response.out.write(jinja2_engine.render('mytba.html', self.template_values))

    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        current_user_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if current_user_id == target_account_id:
            action = self.request.get('action')
    #         if action == "favorite_add":
    #             model = self.request.get('model_key')
    #             if not ValidationHelper.is_valid_model_key(model):
    #                 self.redirect('/account/mytba?error=invalid_model')
    #                 return
    #             favorite = Favorite(parent = ndb.Key(Account, current_user_id), model_key =  model, user_id = current_user_id)
    #            MyTBAHelper.add_favorite(favorite)
    #            self.redirect('/account/mytba')
    #            return
            if action == "favorite_delete":
                model_key = self.request.get('model_key')
                result = MyTBAHelper.remove_favorite(current_user_id, model_key)
                if result == 404:
                    self.redirect('/account/mytba?error=fav_not_found')
                    return
                self.redirect('/account/mytba')
                return
    #         elif action == "subscription_add":
    #             model = self.request.get('model_key')
    #             if not ValidationHelper.is_valid_model_key(model):
    #                 self.redirect('/account/mytba?error=invalid_model')
    #                 return
    #             subs = self.request.get_all('notification_types')
    #             if not subs:
    #                 # No notification types specified. Don't add
    #                 self.redirect('/account/mytba?error=no_sub_types')
    #                 return
    #             subscription = Subscription(parent = ndb.Key(Account, current_user_id), user_id = current_user_id, model_key = model, notification_types = [int(s) for s in subs])
    #             MyTBAHelper.add_subscription(subscription)
    #             self.redirect('/account/mytba')
    #             return
            elif action == "subscription_year_add":
                now = datetime.datetime.now()
                year = self.request.get('year')
                if not "{}".format(now.year) == year:
                    # Can only subscribe to the current year's firehose
                    self.redirect('/account/mytba?error=invalid_year')
                    return
                key = "{}*".format(year)
                subs = self.request.get_all('notification_types')
                if not subs:
                    # No notification types specified. Don't add
                    self.redirect('/account/mytba?error=no_sub_types')
                    return
                subscription = Subscription(parent = ndb.Key(Account, current_user_id), user_id = current_user_id, model_key = key, model_type = ModelType.EVENT, notification_types = [int(s) for s in subs])

                logging.info("{}".format(self.request.get('webhooks_only')))
                MyTBAHelper.add_subscription(subscription)
                self.redirect('/account/mytba')
                return
            elif action == "subscription_delete":
                model_key = self.request.get('model_key')
                result = MyTBAHelper.remove_subscription(current_user_id, model_key)
                if result == 404:
                    self.redirect('/account/mytba?error=sub_not_found')
                    return
                self.redirect('/account/mytba')
                return
        self.redirect('/account/mytba?error=invalid_account')
