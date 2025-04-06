from collections import defaultdict
from typing import Dict, List, Set, Tuple

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.insight import (
    DistrictInsightDistrictData,
    DistrictInsightTeamData,
)
from backend.common.models.keys import DistrictAbbreviation, TeamKey, Year
from backend.common.models.wlt import WLTRecord
from backend.common.queries.district_query import DistrictHistoryQuery
from backend.common.queries.event_query import DistrictEventsQuery
from backend.common.queries.team_query import DistrictTeamsQuery


class InsightsDistrictsHelper:
    @staticmethod
    def make_insight_team_data(
        district_abbreviation: DistrictAbbreviation,
    ) -> Dict[TeamKey, DistrictInsightTeamData]:
        history: List[District] = DistrictHistoryQuery(district_abbreviation).fetch()
        years_participated = defaultdict(list)
        total_district_points = defaultdict(int)
        total_pre_dcmp_district_points = defaultdict(int)
        for district in history:
            if district.year == 2021:
                continue

            for ranking in district.rankings:
                if len(ranking["event_points"]) == 0:
                    continue

                years_participated[ranking["team_key"]].append(district.year)
                for event_points in ranking["event_points"]:
                    # Some of them are floats, no idea why
                    total_district_points[ranking["team_key"]] += int(
                        event_points["total"]
                    )

                    if not event_points["district_cmp"]:
                        total_pre_dcmp_district_points[ranking["team_key"]] += int(
                            event_points["total"]
                        )

        district_event_wins = defaultdict(int)
        dcmp_wins = defaultdict(int)
        team_awards = defaultdict(int)
        individual_awards = defaultdict(int)
        quals_record = defaultdict(lambda: WLTRecord(wins=0, losses=0, ties=0))
        elims_record = defaultdict(lambda: WLTRecord(wins=0, losses=0, ties=0))

        event_futures = []
        for district in history:
            event_futures.append(
                DistrictEventsQuery(district_key=district.key_name).fetch_async()
            )

        event_list: List[Event] = []
        for future in event_futures:
            partial_event_list = future.get_result()
            event_list += partial_event_list

        for event in event_list:
            for award in event.awards:
                for recipient in award.team_list:
                    if award.award_type_enum in [
                        AwardType.WOODIE_FLOWERS,
                        AwardType.DEANS_LIST,
                        AwardType.VOLUNTEER,
                    ]:
                        individual_awards[recipient.string_id()] += 1
                    else:
                        team_awards[recipient.string_id()] += 1

                    if award.award_type_enum == AwardType.WINNER:
                        if award.event_type_enum == EventType.DISTRICT_CMP:
                            dcmp_wins[recipient.string_id()] += 1
                        else:
                            district_event_wins[recipient.string_id()] += 1

            for match in event.matches:
                # Most 2015 matches are ties, so just skip them.
                if match.year == 2015:
                    continue

                counter_dict = (
                    quals_record if match.comp_level == CompLevel.QM else elims_record
                )

                if match.winning_alliance == AllianceColor.RED:
                    for team in match.alliances[AllianceColor.RED]["teams"]:
                        counter_dict[team]["wins"] += 1
                    for team in match.alliances[AllianceColor.BLUE]["teams"]:
                        counter_dict[team]["losses"] += 1
                elif match.winning_alliance == AllianceColor.BLUE:
                    for team in match.alliances[AllianceColor.RED]["teams"]:
                        counter_dict[team]["losses"] += 1
                    for team in match.alliances[AllianceColor.BLUE]["teams"]:
                        counter_dict[team]["wins"] += 1
                else:
                    for team in match.alliances[AllianceColor.RED]["teams"]:
                        counter_dict[team]["ties"] += 1
                    for team in match.alliances[AllianceColor.BLUE]["teams"]:
                        counter_dict[team]["ties"] += 1

        return {
            k: DistrictInsightTeamData(
                district_seasons=len(years_participated[k]),
                total_district_points=total_district_points[k],
                total_pre_dcmp_district_points=total_pre_dcmp_district_points[k],
                district_event_wins=district_event_wins[k],
                dcmp_wins=dcmp_wins[k],
                team_awards=team_awards[k],
                individual_awards=individual_awards[k],
                quals_record=quals_record[k],
                elims_record=elims_record[k],
            )
            for k in years_participated.keys()
        }

    @staticmethod
    def _make_team_deltas(
        yearly_teams: Dict[Year, Set[TeamKey]],
        year_a: Year,
        year_b: Year,
    ) -> Tuple[List[TeamKey], List[TeamKey]]:
        year_a_teams = yearly_teams.get(year_a, set())
        year_b_teams = yearly_teams.get(year_b, set())

        gained_teams = list(year_b_teams - year_a_teams)
        lost_teams = list(year_a_teams - year_b_teams)

        return gained_teams, lost_teams

    @staticmethod
    def make_insight_district_data(
        district_abbreviation: DistrictAbbreviation,
    ) -> DistrictInsightDistrictData:
        history: List[District] = DistrictHistoryQuery(district_abbreviation).fetch()

        yearly_teams = defaultdict(set)
        yearly_events = {}

        for district in history:
            district_teams = DistrictTeamsQuery(district_key=district.key_name).fetch()

            for team in district_teams:
                yearly_teams[district.year].add(team.key_name)

            district_events = DistrictEventsQuery(
                district_key=district.key_name
            ).fetch()

            yearly_events[district.year] = len(district_events)

        yearly_gained_teams = {}
        yearly_lost_teams = {}

        for y in yearly_teams.keys():
            y_gain, y_loss = InsightsDistrictsHelper._make_team_deltas(
                yearly_teams, y - 1, y
            )
            yearly_gained_teams[y] = y_gain
            yearly_lost_teams[y] = y_loss

        return DistrictInsightDistrictData(
            yearly_active_team_count={
                y: len(teams) for y, teams in yearly_teams.items()
            },
            yearly_event_count=yearly_events,
            yearly_gained_teams=yearly_gained_teams,
            yearly_lost_teams=yearly_lost_teams,
        )
