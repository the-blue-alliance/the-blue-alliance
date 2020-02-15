import logging
import os

from controllers.base_controller import LoggedInHandler
from google.appengine.ext.webapp import template
from models.event import Event
from models.match import Match
from models.mobile_client import MobileClient
from helpers.tbans_helper import TBANSHelper


class AdminTBANS(LoggedInHandler):
    """
    TBANS debug panel
    """
    def get(self):
        self._require_admin()

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/tbans_debug.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        user_id = self.user_bundle.account.key.id()

        notification_type = self.request.get('type')
        if notification_type == "alliance_selection":
            event_key = self.request.get('event_key')
            event = Event.get_by_id(event_key)
            if not event:
                self.template_values.update({
                    'error': 'No event for key {}'.format(event_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.alliance_selection(event, user_id)
        elif notification_type == "awards":
            event_key = self.request.get('event_key')
            event = Event.get_by_id(event_key)
            if not event:
                self.template_values.update({
                    'error': 'No event for key {}'.format(event_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.awards(event, user_id)
        elif notification_type == "event_level":
            match_key = self.request.get('match_key')
            match = Match.get_by_id(match_key)
            if not match:
                self.template_values.update({
                    'error': 'No match for key {}'.format(match_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.event_level(match, user_id)
        elif notification_type == "event_schedule":
            event_key = self.request.get('event_key')
            event = Event.get_by_id(event_key)
            if not event:
                self.template_values.update({
                    'error': 'No event for key {}'.format(event_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.event_schedule(event, user_id)
        elif notification_type == "match_score":
            match_key = self.request.get('match_key')
            match = Match.get_by_id(match_key)
            if not match:
                self.template_values.update({
                    'error': 'No match for key {}'.format(match_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.match_score(match, user_id)
        elif notification_type == "match_upcoming":
            match_key = self.request.get('match_key')
            match = Match.get_by_id(match_key)
            if not match:
                self.template_values.update({
                    'error': 'No match for key {}'.format(match_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.match_upcoming(match, user_id)
        elif notification_type == "match_video":
            match_key = self.request.get('match_key')
            match = Match.get_by_id(match_key)
            if not match:
                self.template_values.update({
                    'error': 'No match for key {}'.format(match_key)
                })
                return self.redirect('/admin/tbans')

            TBANSHelper.match_video(match, user_id)
        elif notification_type == "ping":
            clients = MobileClient.clients([user_id])
            for client in clients:
                TBANSHelper.ping(client)

        return self.redirect('/admin/tbans')
