import csv
import json
import logging
import os

import StringIO

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.media_helper import MediaParser
from helpers.media_manipulator import MediaManipulator
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.media import Media


def create_insta_suggestion(account_key_id, team_num, year, insta_url):
        SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=ndb.Key(Account, account_key_id),
            media_url=insta_url,
            team_key="frc{}".format(team_num),
            year_str=str(year),
            default_preferred=True)


class AdminMediaInstagramImport(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/media_import_instagram.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()
        data = self.request.get('images_csv')
        csv_data = csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True)
        for row in csv_data:
            if len(row) != 3:
                continue
            team_num = int(row[0])
            year = int(row[1])
            instagram_url = row[2]
            deferred.defer(
                create_insta_suggestion,
                self.user_bundle.account.key.id(),
                team_num,
                year,
                instagram_url,
                _queue="admin"
            )

        self.redirect('/admin/media/import/instagram')
