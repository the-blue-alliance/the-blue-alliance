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


class AdminMediaDashboard(LoggedInHandler):
    """
    Show stats about Media
    """
    def get(self):
        self._require_admin()
        media_count = Media.query().count()

        self.template_values.update({
            "media_count": media_count
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/media_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMediaDeleteReference(LoggedInHandler):
    def post(self, media_key_name):
        self._require_admin()

        media = Media.get_by_id(media_key_name)

        if media:
            media.references.remove(media.create_reference(
                self.request.get("reference_type"),
                self.request.get("reference_key_name")))

            MediaManipulator.createOrUpdate(media, auto_union=False)

        self.redirect(self.request.get('originating_url'))


class AdminMediaMakePreferred(LoggedInHandler):
    def post(self, media_key_name):
        self._require_admin()

        media = Media.get_by_id(media_key_name)

        media.preferred_references.append(media.create_reference(
            self.request.get("reference_type"),
            self.request.get("reference_key_name")))

        MediaManipulator.createOrUpdate(media)

        self.redirect(self.request.get('originating_url'))


class AdminMediaRemovePreferred(LoggedInHandler):
    def post(self, media_key_name):
        self._require_admin()

        media = Media.get_by_id(media_key_name)

        media.preferred_references.remove(media.create_reference(
            self.request.get("reference_type"),
            self.request.get("reference_key_name")))

        MediaManipulator.createOrUpdate(media, auto_union=False)

        self.redirect(self.request.get('originating_url'))


class AdminMediaAdd(LoggedInHandler):
    def post(self):
        self._require_admin()

        media_dict = MediaParser.partial_media_dict_from_url(self.request.get('media_url').strip())
        if media_dict is not None:
            year_str = self.request.get('year')
            if year_str == '':
                year = None
            else:
                year = int(year_str.strip())

            media = Media(
                id=Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']),
                foreign_key=media_dict['foreign_key'],
                media_type_enum=media_dict['media_type_enum'],
                details_json=media_dict.get('details_json', None),
                year=year,
                references=[Media.create_reference(
                    self.request.get('reference_type'),
                    self.request.get('reference_key'))],
            )
            MediaManipulator.createOrUpdate(media)

        self.redirect(self.request.get('originating_url'))


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
