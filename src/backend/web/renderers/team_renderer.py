import datetime
from typing import cast, Dict, List, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.consts import event_type
from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import COMP_LEVELS
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.helpers.alliance_helper import AllianceHelper
from backend.common.helpers.award_helper import AwardHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.media_helper import MediaHelper
from backend.common.helpers.playlist_helper import PlaylistHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries import (
    award_query,
    district_query,
    event_query,
    match_query,
    media_query,
    team_query,
)


class TeamRenderer:
    @classmethod
    def render_team_details(
        cls, team: Team, year: Year, is_canonical: bool
    ) -> Tuple[Optional[Dict], bool]:
        hof_award_future = award_query.TeamEventTypeAwardsQuery(
            team_key=team.key_name,
            event_type=EventType.CMP_FINALS,
            award_type=AwardType.CHAIRMANS,
        ).fetch_async()
        hof_video_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_VIDEO
        ).fetch_async()
        hof_presentation_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_PRESENTATION
        ).fetch_async()
        hof_essay_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_ESSAY
        ).fetch_async()
        media_future = media_query.TeamYearMediaQuery(
            team_key=team.key_name, year=year
        ).fetch_async()
        social_media_future = media_query.TeamSocialMediaQuery(
            team_key=team.key_name
        ).fetch_async()
        robot_future = Robot.get_by_id_async("{}_{}".format(team.key.id(), year))
        team_districts_future = district_query.TeamDistrictsQuery(
            team_key=team.key_name
        ).fetch_async()
        participation_future = team_query.TeamParticipationQuery(
            team_key=team.key_name
        ).fetch_async()

        hof_awards = hof_award_future.get_result()
        hof_video = hof_video_future.get_result()
        hof_presentation = hof_presentation_future.get_result()
        hof_essay = hof_essay_future.get_result()

        hall_of_fame = {
            "is_hof": len(hof_awards) > 0,
            "years": [award.year for award in hof_awards],
            "media": {
                "video": hof_video[0].youtube_url_link if len(hof_video) > 0 else None,
                "presentation": (
                    hof_presentation[0].youtube_url_link
                    if len(hof_presentation) > 0
                    else None
                ),
                "essay": hof_essay[0].external_link if len(hof_essay) > 0 else None,
            },
        }

        (
            events_sorted,
            matches_by_event_key,
            awards_by_event_key,
            valid_years,
        ) = cls._fetch_data(team, year, return_valid_years=True)
        if not events_sorted:
            return None, False

        district_name = None
        district_abbrev = None
        team_district_points = None

        team_districts = team_districts_future.get_result()
        for district in team_districts:
            # Do not show District Points information for 2021 pages
            if district and district.year == year and district.year != 2021:
                district_abbrev = district.abbreviation
                district_name = district.display_name
                if district.rankings:
                    team_district_points = next(
                        iter(
                            filter(
                                lambda r: r["team_key"] == team.key_name,
                                district.rankings,
                            )
                        ),
                        None,
                    )
                break

        participation = []
        season_wlt_list = []
        offseason_wlt_list = []
        year_match_avg_list = []

        current_event = None
        matches_upcoming = None
        short_cache = False
        for event in events_sorted:
            event_matches = matches_by_event_key.get(event.key, [])
            event_awards = AwardHelper.organize_awards(
                awards_by_event_key.get(event.key, [])
            )
            match_count, matches_organized = MatchHelper.organized_matches(
                event_matches
            )

            if event.now:
                current_event = event
                matches_upcoming = MatchHelper.upcoming_matches(event_matches)

            if event.within_a_day:
                short_cache = True

            if year == 2015:
                display_wlt = None
                match_avg = EventHelper.calculate_team_avg_score(
                    team.key_name, event_matches
                )
                year_match_avg_list.append(match_avg)
                qual_avg, elim_avg, _, _ = match_avg
            else:
                qual_avg = None
                elim_avg = None
                wlt = EventHelper.calculate_wlt(team.key_name, event_matches)
                if event.event_type_enum in event_type.SEASON_EVENT_TYPES:
                    season_wlt_list.append(wlt)
                else:
                    offseason_wlt_list.append(wlt)
                if wlt["wins"] + wlt["losses"] + wlt["ties"] == 0:
                    display_wlt = None
                else:
                    display_wlt = wlt

            team_rank = None
            if event.details and event.details.rankings2:
                for ranking in event.details.rankings2:
                    if ranking["team_key"] == team.key.id():
                        team_rank = ranking["rank"]
                        break

            playlist = PlaylistHelper.generate_playlist_link(
                matches_organized=matches_organized,
                title="{} (Team {})".format(event.name, team.team_number),
                allow_levels=COMP_LEVELS,
            )

            district_points = None
            if team_district_points:
                district_points = next(
                    iter(
                        filter(
                            lambda e: e["event_key"] == event.key_name,
                            team_district_points["event_points"],
                        )
                    ),
                    None,
                )

            alliance, alliance_pick, alliance_size = (
                AllianceHelper.get_alliance_details_and_pick_name(event, team.key_name)
            )

            if alliance and "name" in alliance:
                alliance_status = EventTeamStatusHelper._build_playoff_info(
                    team.key_name,
                    event.details,
                    MatchHelper.organized_matches(event.matches)[1],
                    event.year,
                    event.playoff_type,
                )
                if alliance_status:
                    alliance_status = " and ".join(
                        AllianceHelper.generate_playoff_status_string(
                            alliance_status,
                            alliance_pick,
                            alliance["name"],
                            plural=True,
                            include_record=False,
                        )
                    )
                else:
                    alliance_status = None
            else:
                alliance_status = None

            participation.append(
                {
                    "alliance": alliance,
                    "alliance_status": alliance_status,
                    "alliance_size": alliance_size,
                    "event": event,
                    "matches": matches_organized,
                    "match_count": match_count,
                    "wlt": display_wlt,
                    "qual_avg": qual_avg,
                    "elim_avg": elim_avg,
                    "rank": team_rank,
                    "awards": event_awards,
                    "playlist": playlist,
                    "district_points": district_points,
                }
            )

        season_wlt: Optional[WLTRecord] = None
        offseason_wlt: Optional[WLTRecord] = None
        total_season_matches = 0
        total_offseason_matches = 0
        if year == 2015:
            year_qual_scores = []
            year_elim_scores = []
            for _, _, event_qual_scores, event_elim_scores in year_match_avg_list:
                year_qual_scores += event_qual_scores
                year_elim_scores += event_elim_scores

            year_qual_avg = (
                float(sum(year_qual_scores)) / len(year_qual_scores)
                if year_qual_scores != []
                else None
            )
            year_elim_avg = (
                float(sum(year_elim_scores)) / len(year_elim_scores)
                if year_elim_scores != []
                else None
            )
        else:
            year_qual_avg = None
            year_elim_avg = None

            season_wlt = {"wins": 0, "losses": 0, "ties": 0}
            season_wlt = cast(WLTRecord, season_wlt)

            offseason_wlt = {"wins": 0, "losses": 0, "ties": 0}
            offseason_wlt = cast(WLTRecord, offseason_wlt)

            for wlt in season_wlt_list:
                season_wlt["wins"] += wlt["wins"]
                season_wlt["losses"] += wlt["losses"]
                season_wlt["ties"] += wlt["ties"]

            for wlt in offseason_wlt_list:
                offseason_wlt["wins"] += wlt["wins"]
                offseason_wlt["losses"] += wlt["losses"]
                offseason_wlt["ties"] += wlt["ties"]

            total_season_matches = (
                season_wlt["wins"] + season_wlt["losses"] + season_wlt["ties"]
            )
            total_offseason_matches = (
                offseason_wlt["wins"] + offseason_wlt["losses"] + offseason_wlt["ties"]
            )

        medias_by_slugname = MediaHelper.group_by_slugname(
            [media for media in media_future.get_result()]
        )
        avatar = MediaHelper.get_avatar(media_future.get_result())
        image_medias = MediaHelper.get_images(media_future.get_result())
        social_medias = sorted(
            social_media_future.get_result(), key=MediaHelper.social_media_sorter
        )
        preferred_image_medias = list(
            filter(lambda x: team.key in x.preferred_references, image_medias)
        )

        last_competed = None
        participation_years = participation_future.get_result()
        if len(participation_years) > 0:
            last_competed = max(participation_years)
        current_year = datetime.date.today().year

        template_values = {
            "is_canonical": is_canonical,
            "team": team,
            "participation": participation,
            "year": year,
            "years": valid_years,
            "season_wlt": season_wlt if total_season_matches > 0 else None,
            "offseason_wlt": offseason_wlt if total_offseason_matches > 0 else None,
            "year_qual_avg": year_qual_avg,
            "year_elim_avg": year_elim_avg,
            "current_event": current_event,
            "matches_upcoming": matches_upcoming,
            "medias_by_slugname": medias_by_slugname,
            "avatar": avatar,
            "social_medias": social_medias,
            "image_medias": image_medias,
            "preferred_image_medias": preferred_image_medias,
            "robot": robot_future.get_result(),
            "district_name": district_name,
            "district_abbrev": district_abbrev,
            "last_competed": last_competed,
            "current_year": current_year,
            "max_year": SeasonHelper.get_max_year(),
            "hof": hall_of_fame,
            "team_district_points": team_district_points,
        }

        return template_values, short_cache

    @classmethod
    def render_team_history(cls, team: Team, is_canonical: bool) -> Tuple[Dict, bool]:
        hof_award_future = award_query.TeamEventTypeAwardsQuery(
            team_key=team.key_name,
            event_type=EventType.CMP_FINALS,
            award_type=AwardType.CHAIRMANS,
        ).fetch_async()
        hof_video_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_VIDEO
        ).fetch_async()
        hof_presentation_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_PRESENTATION
        ).fetch_async()
        hof_essay_future = media_query.TeamTagMediasQuery(
            team_key=team.key_name, media_tag=MediaTag.CHAIRMANS_ESSAY
        ).fetch_async()
        award_futures = award_query.TeamAwardsQuery(
            team_key=team.key_name
        ).fetch_async()
        event_futures = event_query.TeamEventsQuery(
            team_key=team.key_name
        ).fetch_async()
        participation_future = team_query.TeamParticipationQuery(
            team_key=team.key_name
        ).fetch_async()
        social_media_future = media_query.TeamSocialMediaQuery(
            team_key=team.key_name
        ).fetch_async()

        hof_awards = hof_award_future.get_result()
        hof_video = hof_video_future.get_result()
        hof_presentation = hof_presentation_future.get_result()
        hof_essay = hof_essay_future.get_result()

        hall_of_fame = {
            "is_hof": len(hof_awards) > 0,
            "years": [award.year for award in hof_awards],
            "media": {
                "video": hof_video[0].youtube_url_link if len(hof_video) > 0 else None,
                "presentation": (
                    hof_presentation[0].youtube_url_link
                    if len(hof_presentation) > 0
                    else None
                ),
                "essay": hof_essay[0].external_link if len(hof_essay) > 0 else None,
            },
        }

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
                matches = match_query.TeamEventMatchesQuery(
                    team.key_name, event.key_name
                ).fetch()
                matches_upcoming = MatchHelper.upcoming_matches(matches)

            if event.within_a_day:
                short_cache = True

            if event.key_name in awards_by_event:
                sorted_awards = AwardHelper.organize_awards(
                    awards_by_event[event.key_name]
                )
            else:
                sorted_awards = []
            event_awards.append((event, sorted_awards))
        event_awards = sorted(
            event_awards,
            key=lambda e_a: (
                e_a[0].start_date
                if e_a[0].start_date
                else datetime.datetime(e_a[0].year, 12, 31)
            ),
        )

        last_competed = None
        participation_years = participation_future.get_result()
        if len(participation_years) > 0:
            last_competed = max(participation_years)
        current_year = datetime.date.today().year

        social_medias = sorted(
            social_media_future.get_result(), key=MediaHelper.social_media_sorter
        )

        template_values = {
            "is_canonical": is_canonical,
            "team": team,
            "event_awards": event_awards,
            "years": sorted(years),
            "social_medias": social_medias,
            "current_event": current_event,
            "matches_upcoming": matches_upcoming,
            "last_competed": last_competed,
            "current_year": current_year,
            "max_year": SeasonHelper.get_max_year(),
            "hof": hall_of_fame,
        }

        return template_values, short_cache

    @classmethod
    def _fetch_data(
        cls, team: Team, year: Year, return_valid_years: bool = False
    ) -> Tuple[
        List[Event],
        Dict[ndb.Key, List[Match]],
        Dict[ndb.Key, List[Award]],
        List[Year],
    ]:
        """
        returns: events_sorted, matches_by_event_key, awards_by_event_key, valid_years
        of a team for a given year
        """
        awards_future = award_query.TeamYearAwardsQuery(
            team_key=team.key_name, year=year
        ).fetch_async()
        events_future = event_query.TeamYearEventsQuery(
            team_key=team.key_name, year=year
        ).fetch_async()
        matches_future = match_query.TeamYearMatchesQuery(
            team_key=team.key_name, year=year
        ).fetch_async()
        if return_valid_years:
            valid_years_future = team_query.TeamParticipationQuery(
                team_key=team.key_name
            ).fetch_async()
        else:
            valid_years_future = None

        events_sorted = sorted(
            events_future.get_result(),
            key=lambda e: (
                e.start_date if e.start_date else datetime.datetime(year, 12, 31)
            ),
        )  # unknown goes last

        matches_by_event_key: Dict[ndb.Key, List[Match]] = {}
        for match in matches_future.get_result():
            if match.event in matches_by_event_key:
                matches_by_event_key[match.event].append(match)
            else:
                matches_by_event_key[match.event] = [match]

        awards_by_event_key: Dict[ndb.Key, List[Award]] = {}
        for award in awards_future.get_result():
            if award.event in awards_by_event_key:
                awards_by_event_key[award.event].append(award)
            else:
                awards_by_event_key[award.event] = [award]

        if return_valid_years and valid_years_future:
            valid_years = sorted(valid_years_future.get_result())
        else:
            valid_years = []

        return events_sorted, matches_by_event_key, awards_by_event_key, valid_years
