import datetime
import os

from google.appengine.ext import ndb

from consts.district_type import DistrictType
from database import award_query, event_query, match_query, media_query, team_query
from database.district_query import DistrictQuery
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher

from helpers.award_helper import AwardHelper
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.media_helper import MediaHelper

from models.award import Award
from models.district import District
from models.event_team import EventTeam
from models.match import Match
from models.robot import Robot

from template_engine import jinja2_engine

from consts.event_type import EventType


class TeamRenderer(object):
    @classmethod
    def render_team_details(cls, handler, team, year, is_canonical):
        media_future = media_query.TeamYearMediaQuery(team.key.id(), year).fetch_async()
        social_media_future = media_query.TeamSocialMediaQuery(team.key.id()).fetch_async()
        robot_future = Robot.get_by_id_async('{}_{}'.format(team.key.id(), year))
        team_districts_future = team_query.TeamDistrictsQuery(team.key.id()).fetch_async()
        participation_future = team_query.TeamParticipationQuery(team.key.id()).fetch_async()

        events_sorted, matches_by_event_key, awards_by_event_key, valid_years = TeamDetailsDataFetcher.fetch(team, year, return_valid_years=True)
        if not events_sorted:
            return None

        participation = []
        season_wlt_list = []
        offseason_wlt_list = []
        year_match_avg_list = []

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

            if year == 2015:
                display_wlt = None
                match_avg = EventHelper.calculateTeamAvgScoreFromMatches(team.key_name, event_matches)
                year_match_avg_list.append(match_avg)
                qual_avg, elim_avg, _, _ = match_avg
            else:
                qual_avg = None
                elim_avg = None
                wlt = EventHelper.calculateTeamWLTFromMatches(team.key_name, event_matches)
                if event.event_type_enum in EventType.SEASON_EVENT_TYPES:
                    season_wlt_list.append(wlt)
                else:
                    offseason_wlt_list.append(wlt)
                if wlt["win"] + wlt["loss"] + wlt["tie"] == 0:
                    display_wlt = None
                else:
                    display_wlt = wlt

            team_rank = None
            if event.rankings:
                for element in event.rankings:
                    if str(element[1]) == str(team.team_number):
                        team_rank = element[0]
                        break

            participation.append({'event': event,
                                  'matches': matches_organized,
                                  'wlt': display_wlt,
                                  'qual_avg': qual_avg,
                                  'elim_avg': elim_avg,
                                  'rank': team_rank,
                                  'awards': event_awards})

        season_wlt = None
        offseason_wlt = None
        if year == 2015:
            year_wlt = None
            year_qual_scores = []
            year_elim_scores = []
            for _, _, event_qual_scores, event_elim_scores in year_match_avg_list:
                year_qual_scores += event_qual_scores
                year_elim_scores += event_elim_scores

            year_qual_avg = float(sum(year_qual_scores)) / len(year_qual_scores) if year_qual_scores != [] else None
            year_elim_avg = float(sum(year_elim_scores)) / len(year_elim_scores) if year_elim_scores != [] else None
        else:
            year_qual_avg = None
            year_elim_avg = None
            season_wlt = {"win": 0, "loss": 0, "tie": 0}
            offseason_wlt = {"win": 0, "loss": 0, "tie": 0}

            for wlt in season_wlt_list:
                season_wlt["win"] += wlt["win"]
                season_wlt["loss"] += wlt["loss"]
                season_wlt["tie"] += wlt["tie"]
            if season_wlt["win"] + season_wlt["loss"] + season_wlt["tie"] == 0:
                season_wlt = None

            for wlt in offseason_wlt_list:
                offseason_wlt["win"] += wlt["win"]
                offseason_wlt["loss"] += wlt["loss"]
                offseason_wlt["tie"] += wlt["tie"]
            if offseason_wlt["win"] + offseason_wlt["loss"] + offseason_wlt["tie"] == 0:
                offseason_wlt = None

        medias_by_slugname = MediaHelper.group_by_slugname([media for media in media_future.get_result()])
        image_medias = MediaHelper.get_images(media_future.get_result())
        social_medias = sorted(social_media_future.get_result(), key=MediaHelper.social_media_sorter)
        preferred_image_medias = filter(lambda x: team.key in x.preferred_references, image_medias)

        district_name = None
        district_abbrev = None
        team_districts = team_districts_future.get_result()
        for district in team_districts:
            if district.year == year:
                district_abbrev = district.abbreviation
                district_name = district.display_name

        last_competed = None
        participation_years = participation_future.get_result()
        if len(participation_years) > 0:
            last_competed = max(participation_years)
        current_year = datetime.date.today().year

        handler.template_values.update({
            "is_canonical": is_canonical,
            "team": team,
            "participation": participation,
            "year": year,
            "years": valid_years,
            "season_wlt": season_wlt,
            "offseason_wlt": offseason_wlt,
            "year_qual_avg": year_qual_avg,
            "year_elim_avg": year_elim_avg,
            "current_event": current_event,
            "matches_upcoming": matches_upcoming,
            "medias_by_slugname": medias_by_slugname,
            "social_medias": social_medias,
            "image_medias": image_medias,
            "preferred_image_medias": preferred_image_medias,
            "robot": robot_future.get_result(),
            "district_name": district_name,
            "district_abbrev": district_abbrev,
            "last_competed": last_competed,
            "current_year": current_year,
        })

        if short_cache:
            handler._cache_expiration = handler.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('team_details.html', handler.template_values)

    @classmethod
    def render_team_history(cls, handler, team, is_canonical):
        award_futures = award_query.TeamAwardsQuery(team.key.id()).fetch_async()
        event_futures = event_query.TeamEventsQuery(team.key.id()).fetch_async()
        participation_future = team_query.TeamParticipationQuery(team.key.id()).fetch_async()
        social_media_future = media_query.TeamSocialMediaQuery(team.key.id()).fetch_async()

        awards_by_event = {}
        for award in award_futures.get_result():
            if award.event.id() not in awards_by_event:
                awards_by_event[award.event.id()] = [award]
            else:
                awards_by_event[award.event.id()].append(award)

        event_awards = []
        current_event = None
        matches_upcoming = None
        short_cache = False
        years = set()
        for event in event_futures.get_result():
            years.add(event.year)
            if event.now:
                current_event = event
                matches = match_query.TeamEventMatchesQuery(team.key.id(), event.key.id()).fetch()
                matches_upcoming = MatchHelper.upcomingMatches(matches)

            if event.within_a_day:
                short_cache = True

            if event.key_name in awards_by_event:
                sorted_awards = AwardHelper.organizeAwards(awards_by_event[event.key_name])
            else:
                sorted_awards = []
            event_awards.append((event, sorted_awards))
        event_awards = sorted(event_awards, key=lambda (e, _): e.start_date if e.start_date else datetime.datetime(e.year, 12, 31))

        last_competed = None
        participation_years = participation_future.get_result()
        if len(participation_years) > 0:
            last_competed = max(participation_years)
        current_year = datetime.date.today().year

        social_medias = sorted(social_media_future.get_result(), key=MediaHelper.social_media_sorter)

        handler.template_values.update({
            'is_canonical': is_canonical,
            'team': team,
            'event_awards': event_awards,
            'years': sorted(years),
            "social_medias": social_medias,
            'current_event': current_event,
            'matches_upcoming': matches_upcoming,
            'last_competed': last_competed,
            'current_year': current_year
        })

        if short_cache:
            handler._cache_expiration = handler.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('team_history.html', handler.template_values)
