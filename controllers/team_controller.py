import datetime
import os
import string

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from database import team_query
from models.team import Team

from renderers.team_renderer import TeamRenderer
from template_engine import jinja2_engine


def normalize_team_number(team_number):
    """Remove leading 0s from a team number, keeping any suffixes."""
    suffix = team_number.lstrip(string.digits)
    number = team_number[:len(team_number) - len(suffix)]
    return str(int(number)) + suffix


def base_team_number(team_number):
    """Strip any suffixes from a team number."""
    return "".join(filter(str.isdigit, team_number))


class TeamList(CacheableHandler):
    VALID_PAGES = [1, 2, 3, 4, 5, 6, 7, 8]
    CACHE_VERSION = 2
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

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(page)
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

        teams_1 = team_query.TeamListQuery(2 * (page - 1)).fetch_async()
        teams_2 = team_query.TeamListQuery(2 * (page - 1) + 1).fetch_async()
        teams = teams_1.get_result() + teams_2.get_result()

        num_teams = len(teams)
        middle_value = num_teams / 2
        if num_teams % 2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]

        self.template_values.update({
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "page_labels": page_labels,
            "cur_page_label": cur_page_label,
            "current_page": page
        })

        return jinja2_engine.render('team_list.html', self.template_values)


class TeamCanonical(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "team_canonical_{}"  # (team_number)

    def __init__(self, *args, **kw):
        super(TeamCanonical, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number):
        # /team/0201 should redirect to /team/201
        normalized_team = normalize_team_number(team_number)
        if normalized_team != team_number:
            return self.redirect("/team/%s" % normalized_team)

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format("frc{}".format(team_number))
        super(TeamCanonical, self).get(team_number)

    def _render(self, team_number):
        team = Team.get_by_id("frc{}".format(base_team_number(team_number)))
        if not team:
            self.abort(404)

        year = datetime.datetime.now().year

        rendered_result = TeamRenderer.render_team_details(self, team, "frc{}".format(team_number), year, True)
        if rendered_result is None:
            return TeamRenderer.render_team_history(self, team, "frc{}".format(team_number), True)
        else:
            return rendered_result


class TeamDetail(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "team_detail_{}_{}"  # (team_number, year)

    def __init__(self, *args, **kw):
        super(TeamDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number, year):
        # /team/0201 should redirect to /team/201
        normalized_team = normalize_team_number(team_number)
        if normalized_team != team_number:
            return self.redirect("/team/%s/%s" % (normalized_team, year))

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format("frc{}".format(team_number), year)
        super(TeamDetail, self).get(team_number, year)

    def _render(self, team_number, year):
        team = Team.get_by_id("frc{}".format(base_team_number(team_number)))
        if not team:
            self.abort(404)

        rendered_result = TeamRenderer.render_team_details(self, team, "frc{}".format(team_number), int(year), False)
        if rendered_result is None:
            self.abort(404)
        else:
            return rendered_result


class TeamHistory(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "team_history_{}"  # (team_number)

    def __init__(self, *args, **kw):
        super(TeamHistory, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, team_number):
        # /team/0604/history should redirect to /team/604/history
        normalized_team = normalize_team_number(team_number)
        if normalized_team != team_number:
            return self.redirect("/team/%s/history" % normalized_team)

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format("frc" + team_number)
        super(TeamHistory, self).get(team_number)

    def _render(self, team_number):
        team = Team.get_by_id("frc{}".format(base_team_number(team_number)))
        if not team:
            self.abort(404)

        return TeamRenderer.render_team_history(self, team, "frc{}".format(team_number), False)
