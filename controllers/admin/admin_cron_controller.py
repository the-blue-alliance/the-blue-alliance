from datetime import date
import logging
import os
import re

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.client_type import ClientType
from controllers.base_controller import LoggedInHandler
from helpers.notification_sender import NotificationSender
from models.mobile_client import MobileClient
from models.subscription import Subscription
from notifications.ping import PingNotification


class AdminMobileClearEnqueue(LoggedInHandler):
    """
    Clears mobile clients with duplicate client_ids
    Will leave the most recently updated one
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/do/clear_mobile_duplicates',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMobileClearDo(LoggedInHandler):
    """
    Fetch all mobile clients, order by messaging ID, then update time (desc).
    If the current client has the same ID as the last one (which is always going to be newer), mark the current one to be removed
    """
    def get(self):
        clients = MobileClient.query().fetch()
        clients = sorted(clients, key=lambda x: (x.messaging_id, x.updated))
        last = None
        to_remove = []
        last = None
        for client in clients:
            if last is not None and client.messaging_id == last.messaging_id:
                logging.info("Removing")
                to_remove.append(client.key)
            last = client
        count = len(to_remove)
        if to_remove:
            ndb.delete_multi(to_remove)
        logging.info("Removed {} duplicate mobile clients".format(count))
        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_clear_do.html')
        self.response.out.write(template.render(path, template_values))


class AdminSubsClearEnqueue(LoggedInHandler):
    """
    Removes subscriptions to past years' things
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/do/clear_old_subs',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/subs_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminSubsClearDo(LoggedInHandler):
    def get(self):
        year = date.today().year - 1
        # Compile key regex
        # Matches event (2014ctgro), team@event (frc2014_2014ctgro)
        ps = "\A{}[a-z]+|_{}[a-z]+".format(year, year)
        logging.info("Pattern: {}".format(ps))
        p = re.compile(ps)

        subs = Subscription.query().fetch()
        to_delete = []
        for sub in subs:
            if p.match(sub.model_key):
                to_delete.append(sub.key)
        count = len(to_delete)
        if to_delete:
            ndb.delete_multi(to_delete)
        logging.info("Removed {} old subscriptions".format(count))
        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/subs_clear_do.html')
        self.response.out.write(template.render(path, template_values))


class AdminWebhooksClearEnqueue(LoggedInHandler):
    """
    Tries to ping every webhook and removes ones that don't respond
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/do/clear_old_webhooks',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/webhooks_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminWebhooksClearDo(LoggedInHandler):
    def get(self):
        webhooks = MobileClient.query(MobileClient.client_type == ClientType.WEBHOOK).fetch()
        failures = []

        notification = PingNotification()._render_webhook()

        for key in webhooks:
            if not NotificationSender.send_webhook(notification, [(key.messaging_id, key.secret)]):
                failures.append(key.key)

        count = len(failures)
        if failures:
            ndb.delete_multi(failures)
        logging.info("Deleted {} broken webhooks".format(count))

        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/webhooks_clear_do.html')
        self.response.out.write(template.render(path, template_values))
