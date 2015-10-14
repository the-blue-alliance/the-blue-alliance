import os
import json
import re
import logging
import datetime

from google.appengine.api import memcache
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from database.database_query import DatabaseQuery
from models.account import Account
from models.suggestion import Suggestion


class AdminMain(LoggedInHandler):
    def get(self):
        self._require_admin()

        self.template_values['memcache_stats'] = memcache.get_stats()
        self.template_values['databasequery_stats'] = {
            'hits': sum(filter(None, [memcache.get(key) for key in DatabaseQuery.DATABASE_HITS_MEMCACHE_KEYS])),
            'misses': sum(filter(None, [memcache.get(key) for key in DatabaseQuery.DATABASE_MISSES_MEMCACHE_KEYS]))
        }

        # Gets the 5 recently created users
        users = Account.query().order(-Account.created).fetch(5)
        self.template_values['users'] = users

        # Retrieves the number of pending suggestions
        video_suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "match").count()
        self.template_values['video_suggestions'] = video_suggestions

        webcast_suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "event").count()
        self.template_values['webcast_suggestions'] = webcast_suggestions

        media_suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "media").count()
        self.template_values['media_suggestions'] = media_suggestions

        # version info
        try:
            fname = os.path.join(os.path.dirname(__file__), '../../version_info.json')

            with open(fname, 'r') as f:
                data = json.loads(f.read().replace('\r\n', '\n'))

            self.template_values['git_branch_name'] = data['git_branch_name']
            self.template_values['build_time'] = data['build_time']

            commit_parts = re.split("[\n]+", data['git_last_commit'])
            self.template_values['commit_hash'] = commit_parts[0].split(" ")
            self.template_values['commit_author'] = commit_parts[1]
            self.template_values['commit_date'] = commit_parts[2]
            self.template_values['commit_msg'] = commit_parts[3]

        except Exception, e:
            logging.warning("version_info.json parsing failed: %s" % e)
            pass

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/index.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminDebugHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        self.template_values['cur_year'] = datetime.datetime.now().year
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/debug.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminTasksHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/tasks.html')
        self.response.out.write(template.render(path, self.template_values))
