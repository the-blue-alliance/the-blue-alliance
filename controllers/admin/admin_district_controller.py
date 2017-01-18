import os
from datetime import datetime

from google.appengine.ext.webapp import template

import tba_config
from controllers.base_controller import LoggedInHandler
from helpers.district_manipulator import DistrictManipulator
from models.district import District


class AdminDistrictList(LoggedInHandler):
    """
    List all Districts.
    """
    VALID_YEARS = range(2009, tba_config.MAX_YEAR + 1)

    def get(self, year=None):
        self._require_admin()

        if year:
            year = int(year)
        else:
            year = datetime.now().year

        districts = District.query(District.year == year).fetch(10000)

        self.template_values.update({
            "valid_years": self.VALID_YEARS,
            "selected_year": year,
            "districts": districts,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/district_list.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminDistrictEdit(LoggedInHandler):
    """
    Modify a district
    """

    def get(self, district_key):
        self._require_admin()

        district = District.get_by_id(district_key)
        self.template_values.update({
            "district": district,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/district_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, district_key):
        self._require_admin()

        district = District(
            id=District.renderKeyName(self.request.get("year"), self.request.get("abbreviation")),
            year=int(self.request.get("year")),
            abbreviation=self.request.get("abbreviation"),
            display_name=self.request.get("display_name"),
            elasticsearch_name=self.request.get("elasticsearch_name"),
        )
        DistrictManipulator.createOrUpdate(district)

        self.redirect('/admin/districts/' + self.request.get("year"))


class AdminDistrictCreate(LoggedInHandler):
    """
    Create an District. POSTs to AdminDistrictEdit.
    """
    def get(self):
        self._require_admin()

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/district_create.html')
        self.response.out.write(template.render(path, self.template_values))
