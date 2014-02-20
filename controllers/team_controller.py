import datetime
import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher
from models.event_team import EventTeam
from models.match import Match
from models.team import Team
from models.award import Award

# The view of a list of teams.


class TeamList(CacheableHandler):

    VALID_PAGES = [1, 2, 3, 4, 5, 6]

    def __init__(self, *args, **kw):
        super(TeamList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "team_list_{}"  # (page)
        self._cache_version = 1

    def get(self, page='1'):
        if page == '':
            return self.redirect("/teams")
        page = int(page)
        if page not in self.VALID_PAGES:
            self.abort(404)

        self._cache_key = self._cache_key.format(page)
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

# The view of a single Team.


class TeamDetail(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(TeamDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "team_detail_{}_{}_{}"  # (team_number, year, explicit_year)
        self._cache_version = 2

    def get(self, team_number, year=None, explicit_year=False):

        # /team/0201 should redirect to /team/201
        try:
            if str(int(team_number)) != team_number:
                if year is None:
                    return self.redirect("/team/%s" % int(team_number))
                else:
                    return self.redirect("/team/%s/%s" % (int(team_number), year))
        except ValueError, e:
            logging.info("%s", e)
            self.abort(404)

        if type(year) == str:
            try:
                year = int(year)
            except ValueError, e:
                logging.info("%s", e)
                return self.redirect("/team/%s" % team_number)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False

        self._cache_key = self._cache_key.format("frc" + team_number, year, explicit_year)
        super(TeamDetail, self).get(team_number, year, explicit_year)

    def _render(self, team_number, year=None, explicit_year=False):
        team = Team.get_by_id("frc" + team_number)
        if not team:
            self.abort(404)

        events_sorted, matches_by_event_key, awards_by_event_key, valid_years = TeamDetailsDataFetcher.fetch(team, year, return_valid_years=True)
        if not events_sorted:
            self.abort(404)

        participation = []
        year_wlt_list = []

        current_event = None
        matches_upcoming = None
        short_cache = False
        for event in events_sorted:
            event_matches = matches_by_event_key.get(event.key, [])
            event_awards = AwardHelper.organizeAwards(awards_by_event_key.get(event.key, []))
            matches_organized = MatchHelper.organizeMatches(event_matches)

            if event.now:
                current_event = event
                matches_upcoming = MatchHelper.upcomingMatches(event_matches)

            if event.within_a_day:
                short_cache = True

            wlt = EventHelper.calculateTeamWLTFromMatches(team.key_name, event_matches)
            year_wlt_list.append(wlt)
            if wlt["win"] + wlt["loss"] + wlt["tie"] == 0:
                display_wlt = None
            else:
                display_wlt = wlt

            team_rank = None
            if event.rankings:
                for element in event.rankings:
                    if element[1] == team_number:
                        team_rank = element[0]
                        break

            participation.append({'event': event,
                                   'matches': matches_organized,
                                   'wlt': display_wlt,
                                   'rank': team_rank,
                                   'awards': event_awards})

        year_wlt = {"win": 0, "loss": 0, "tie": 0}
        for wlt in year_wlt_list:
            year_wlt["win"] += wlt["win"]
            year_wlt["loss"] += wlt["loss"]
            year_wlt["tie"] += wlt["tie"]
        if year_wlt["win"] + year_wlt["loss"] + year_wlt["tie"] == 0:
            year_wlt = None

        template_values = {"explicit_year": explicit_year,
                            "team": team,
                            "participation": participation,
                            "year": year,
                            "years": valid_years,
                            "year_wlt": year_wlt,
                            "current_event": current_event,
                            "matches_upcoming": matches_upcoming}

        if short_cache:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/team_details.html')
        return template.render(path, template_values)


class TeamHistory(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(TeamHistory, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "team_history_{}"  # (team_number)
        self._cache_version = 2

    def get(self, team_number):
        # /team/0604/history should redirect to /team/604/history
        try:
            if str(int(team_number)) != team_number:
                return self.redirect("/team/%s/history" % int(team_number))

        except ValueError, e:
            logging.info("%s", e)
            self.abort(404)

        self._cache_key = self._cache_key.format("frc" + team_number)
        super(TeamHistory, self).get(team_number)

    def _render(self, team_number):
        team = Team.get_by_id("frc" + team_number)

        if not team:
            self.abort(404)

        event_team_keys_future = EventTeam.query(EventTeam.team == team.key).fetch_async(1000, keys_only=True)
        award_keys_future = Award.query(Award.team_list == team.key).fetch_async(1000, keys_only=True)

        event_teams_futures = ndb.get_multi_async(event_team_keys_future.get_result())
        awards_futures = ndb.get_multi_async(award_keys_future.get_result())

        event_keys = [event_team_future.get_result().event for event_team_future in event_teams_futures]
        events_futures = ndb.get_multi_async(event_keys)

        awards_by_event = {}
        for award_future in awards_futures:
            award = award_future.get_result()
            if award.event.id() not in awards_by_event:
                awards_by_event[award.event.id()] = [award]
            else:
                awards_by_event[award.event.id()].append(award)

        event_awards = []
        current_event = None
        matches_upcoming = None
        short_cache = False
        for event_future in events_futures:
            event = event_future.get_result()
            if event.now:
                current_event = event

                team_matches_future = Match.query(Match.event == event.key, Match.team_key_names == team.key_name)\
                  .fetch_async(500, keys_only=True)
                matches = ndb.get_multi(team_matches_future.get_result())
                matches_upcoming = MatchHelper.upcomingMatches(matches)

            if event.within_a_day:
                short_cache = True

            if event.key_name in awards_by_event:
                sorted_awards = AwardHelper.organizeAwards(awards_by_event[event.key_name])
            else:
                sorted_awards = []
            event_awards.append((event, sorted_awards))
        event_awards = sorted(event_awards, key=lambda (e, _): e.start_date if e.start_date else datetime.datetime(e.year, 12, 31))

        years = sorted(set([et.get_result().year for et in event_teams_futures if et.get_result().year is not None]))

        template_values = {'team': team,
                           'event_awards': event_awards,
                           'years': years,
                           'current_event': current_event,
                           'matches_upcoming': matches_upcoming}

        if short_cache:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/team_history.html')
        return template.render(path, template_values)
