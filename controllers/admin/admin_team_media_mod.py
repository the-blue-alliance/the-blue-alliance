import csv
import os
import StringIO
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.account import Account
from models.team_admin_access import TeamAdminAccess


class AdminTeamMediaModCodeList(LoggedInHandler):
    """
    List all active mod tokens
    """
    MAX_PAGE = 10  # Everything after this will be shown on one page
    PAGE_SIZE = 1000

    def get(self, year=None, page_num=0):
        self._require_admin()
        page_num = int(page_num)

        if year:
            year = int(year)
        else:
            year = datetime.now().year

        if page_num < self.MAX_PAGE:
            start = self.PAGE_SIZE * page_num
            end = start + self.PAGE_SIZE
            auth_codes = TeamAdminAccess.query(
                TeamAdminAccess.year == year,
                TeamAdminAccess.team_number >= start,
                TeamAdminAccess.team_number < end).order(
                    TeamAdminAccess.team_number).fetch()
        else:
            start = self.PAGE_SIZE * self.MAX_PAGE
            auth_codes = TeamAdminAccess.query(
                TeamAdminAccess.team_number >= start).order(
                    TeamAdminAccess.team_number).fetch()

        page_labels = []
        for page in xrange(self.MAX_PAGE):
            if page == 0:
                page_labels.append('1-999')
            else:
                page_labels.append('{}\'s'.format(1000 * page))
        page_labels.append('{}+'.format(1000 * self.MAX_PAGE))

        self.template_values.update({
            "year": year,
            "auth_codes": auth_codes,
            "page_labels": page_labels,
        })

        path = os.path.join(
            os.path.dirname(__file__),
            '../../templates/admin/team_media_mod_list.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminTeamMediaModCodeAdd(LoggedInHandler):
    def get(self, year=None, page_num=0):
        self._require_admin()

        path = os.path.join(
            os.path.dirname(__file__),
            '../../templates/admin/team_media_mod_add.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        year = int(self.request.get("year"))
        auth_codes_csv = self.request.get("auth_codes_csv")

        csv_data = list(
            csv.reader(StringIO.StringIO(auth_codes_csv), delimiter=','))
        auth_codes = []
        for row in csv_data:
            team_number = int(row[0])
            auth_codes.append(
                TeamAdminAccess(
                    id=TeamAdminAccess.renderKeyName(team_number, year),
                    team_number=team_number,
                    year=year,
                    access_code=row[1],
                    expiration=datetime(year=year, month=7, day=1),
                ))
        ndb.put_multi(auth_codes)
        self.redirect('/admin/media/modcodes/list/{}'.format(year))


class AdminTeamMediaModCodeEdit(LoggedInHandler):
    def get(self, team_number, year):
        self._require_admin()
        team_number = int(team_number)
        year = int(year)

        access = TeamAdminAccess.query(
            TeamAdminAccess.year == year,
            TeamAdminAccess.team_number == team_number).fetch(1)
        if not access:
            self.abort(404)
            return

        access = access[0]
        account_email = None
        if access.account:
            account = access.account.get()
            account_email = account.email
        self.template_values.update({
            'access': access,
            'account_email': account_email,
        })
        path = os.path.join(
            os.path.dirname(__file__),
            '../../templates/admin/team_media_mod_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, team_number, year):
        self._require_admin()
        team_number = int(team_number)
        year = int(year)

        access = TeamAdminAccess.query(
            TeamAdminAccess.year == year,
            TeamAdminAccess.team_number == team_number).fetch()
        if not access:
            self.abort(404)
            return

        access = access[0]
        access_code = self.request.get('access_code')
        expiration = self.request.get('expiration')
        account_email = self.request.get('account_email')

        account = None
        if account_email:
            accounts = Account.query(Account.email == account_email).fetch(1)
            if accounts:
                account = accounts[0]

        access.access_code = access_code
        access.expiration = datetime.strptime(expiration, "%Y-%m-%d")
        access.account = account.key if account else None
        access.put()

        self.redirect('/admin/media/modcodes/edit/{}/{}'.format(team_number, year))
