import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

from models.team import Team

from renderers.team_renderer import TeamRenderer


class TeamList(CacheableHandler):
    VALID_PAGES = [1, 2, 3, 4, 5, 6]
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_list_{}"  # (page)

    def __init__(self, *args, **kw):
        super(TeamList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def get(self, page='1'):
        if page == '':
            return self.redirect("/teams")
        page = int(page)
        if page not in self.VALID_PAGES:
            self.abort(404)

        self._cache_key = self.CACHE_KEY_FORMAT.format(page)
        super(TeamList, self).get(page)

    def _render(self, page=''):
        page_labels = []
        for curPage in self.VALID_PAGES:
            if curPage == 1:
                label = '1-999'
            else:
                label = "{}'s".format((curPage - 1) * 1000)
            page_labels.append(label)
            if curPage == page:
                cur_page_label = label

        start = (page - 1) * 1000
        stop = start + 999

        if start == 0:
            start = 1

        team_keys = Team.query().order(Team.team_number).filter(
          Team.team_number >= start).filter(Team.team_number < stop).fetch(10000, keys_only=True)
        teams = ndb.get_multi(team_keys)

        num_teams = len(teams)
        middle_value = num_teams / 2
        if num_teams % 2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]

        template_values = {
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "page_labels": page_labels,
            "cur_page_label": cur_page_label,
            "current_page": page
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/team_list.html')
        return template.render(path, template_values)


class TeamCanonical(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "team_canonical_{}"  # (team_number)

    def __init__(self, *args, **kw):
        super(TeamCanonical, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number):
        # /team/0201 should redirect to /team/201
        if str(int(team_number)) != team_number:
            return self.redirect("/team/%s" % int(team_number))

        self._cache_key = self.CACHE_KEY_FORMAT.format("frc{}".format(team_number))
        super(TeamCanonical, self).get(team_number)

    def _render(self, team_number):
        team = Team.get_by_id("frc{}".format(team_number))
        if not team:
            self.abort(404)

        year = datetime.datetime.now().year

        rendered_result = TeamRenderer.render_team_details(self, team, year, True)
        if rendered_result is None:
            return TeamRenderer.render_team_history(self, team, True)
        else:
            return rendered_result


class TeamDetail(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_detail_{}_{}"  # (team_number, year)

    def __init__(self, *args, **kw):
        super(TeamDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number, year):
        # /team/0201 should redirect to /team/201
        if str(int(team_number)) != team_number:
            return self.redirect("/team/%s/%s" % (int(team_number), year))

        self._cache_key = self.CACHE_KEY_FORMAT.format("frc{}".format(team_number), year)
        super(TeamDetail, self).get(team_number, year)

    def _render(self, team_number, year):
        team = Team.get_by_id("frc{}".format(team_number))
        if not team:
            self.abort(404)

        rendered_result = TeamRenderer.render_team_details(self, team, int(year), False)
        if rendered_result is None:
            self.abort(404)
        else:
            return rendered_result


class TeamHistory(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_history_{}"  # (team_number)

    def __init__(self, *args, **kw):
        super(TeamHistory, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number):
        # /team/0604/history should redirect to /team/604/history
        if str(int(team_number)) != team_number:
            return self.redirect("/team/%s/history" % int(team_number))

        self._cache_key = self.CACHE_KEY_FORMAT.format("frc" + team_number)
        super(TeamHistory, self).get(team_number)

    def _render(self, team_number):
        team = Team.get_by_id("frc" + team_number)
        if not team:
            self.abort(404)

        return TeamRenderer.render_team_history(self, team, False)
