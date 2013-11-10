import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.media_helper import MediaHelper
from helpers.media_manipulator import MediaManipulator
from models.media import Media
from models.team import Team


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


class AdminMediaAdd(LoggedInHandler):
    REFERENCE_MAP = {
        'team': Team
    }

    def post(self):
        self._require_admin()

        media_dict = MediaHelper.partial_media_dict_from_url(self.request.get('media_url').strip())
        year_str = self.request.get('year')
        if year_str == '':
            year = None
        else:
            year = int(year_str.strip())

        media = Media(
            id=Media.render_key_name(media_dict['media_type_enum'], media_dict['media_id']),
            media_id=media_dict['media_id'],
            media_type_enum=media_dict['media_type_enum'],
            details_json=media_dict.get('details_json', None),
            year=year,
            references=[ndb.Key(self.REFERENCE_MAP[self.request.get('reference_type')],
                                self.request.get('reference_key'))],
        )
        MediaManipulator.createOrUpdate(media)

        self.redirect(self.request.get('originating_url'))
