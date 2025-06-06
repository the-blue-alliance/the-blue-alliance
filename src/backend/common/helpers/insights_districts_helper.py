from collections import defaultdict
from typing import Dict, List, Set, Tuple

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType, BLUE_BANNER_AWARDS
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.us_states import STATE_ABBREV_TO_NAME
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.insight import (
    DistrictInsightDistrictData,
    DistrictInsightDistrictRegionData,
    DistrictInsightTeamData,
)
from backend.common.models.keys import DistrictAbbreviation, TeamKey, Year
from backend.common.models.team import Team
from backend.common.models.wlt import WLTRecord
from backend.common.queries.district_query import DistrictHistoryQuery
from backend.common.queries.event_query import (
    CmpDivisionsInYearQuery,
    DistrictChampsInYearQuery,
    DistrictEventsQuery,
)
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

        # Build event lists
        event_futures = []
        for district in history:
            event_futures.append(
                DistrictEventsQuery(district_key=district.key_name).fetch_async()
            )

        district_event_list: List[Event] = []
        for future in event_futures:
            partial_event_list = future.get_result()
            district_event_list += partial_event_list

        dcmp_event_futures = []
        for district in history:
            dcmp_event_futures.append(
                DistrictChampsInYearQuery(year=district.year).fetch_async()
            )

        dcmp_event_list: List[Event] = []
        for future in dcmp_event_futures:
            partial_event_list = future.get_result()
            dcmp_event_list += partial_event_list

        cmp_event_futures = []
        for district in history:
            cmp_event_futures.append(
                CmpDivisionsInYearQuery(year=district.year).fetch_async()
            )

        cmp_event_list: List[Event] = []
        for future in cmp_event_futures:
            partial_event_list = future.get_result()
            cmp_event_list += partial_event_list

        # Stat tracking dicts
        district_event_wins = defaultdict(int)
        dcmp_wins = defaultdict(int)
        team_awards = defaultdict(int)
        individual_awards = defaultdict(int)
        blue_banners = defaultdict(int)
        quals_record = defaultdict(lambda: WLTRecord(wins=0, losses=0, ties=0))
        elims_record = defaultdict(lambda: WLTRecord(wins=0, losses=0, ties=0))
        district_event_per_year_count = defaultdict(lambda: defaultdict(int))
        total_matches_played = defaultdict(int)
        dcmp_appearances = defaultdict(int)
        cmp_appearances = defaultdict(int)

        for event in district_event_list:
            for team in event.teams:
                if event.event_type_enum == EventType.DISTRICT:
                    district_event_per_year_count[team.key_name][event.year] += 1

            for award in event.awards:
                for recipient in award.team_list:
                    if award.award_type_enum in BLUE_BANNER_AWARDS:
                        blue_banners[recipient.string_id()] += 1

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
                if not match.has_been_played:
                    continue

                for color in AllianceColor:
                    for team in match.alliances[color]["teams"]:
                        total_matches_played[team] += 1

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
                elif (
                    match.year != 2015
                ):  # Most 2015 matches are ties, so just skip those
                    for team in match.alliances[AllianceColor.RED]["teams"]:
                        counter_dict[team]["ties"] += 1
                    for team in match.alliances[AllianceColor.BLUE]["teams"]:
                        counter_dict[team]["ties"] += 1

        for dcmp_event in dcmp_event_list:
            for team in dcmp_event.teams:
                dcmp_appearances[team.key_name] += 1

        for cmp_event in cmp_event_list:
            for team in cmp_event.teams:
                cmp_appearances[team.key_name] += 1

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
                blue_banners=blue_banners[k],
                in_district_extra_play_count=sum(
                    [
                        max(0, district_event_per_year_count[k][y] - 2)
                        for y in district_event_per_year_count[k].keys()
                    ]
                ),
                total_matches_played=total_matches_played[k],
                dcmp_appearances=dcmp_appearances[k],
                cmp_appearances=cmp_appearances[k],
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

        district_yearly_teams = defaultdict(list)
        district_yearly_events = defaultdict(list)
        region_yearly_teams = defaultdict(lambda: defaultdict(list))
        region_yearly_events = defaultdict(lambda: defaultdict(list))

        for district_year in history:
            district_teams = DistrictTeamsQuery(
                district_key=district_year.key_name
            ).fetch()
            district_events = DistrictEventsQuery(
                district_key=district_year.key_name
            ).fetch()

            for team in district_teams:
                district_yearly_teams[district_year.year].append(team)
                region_yearly_teams[get_state_or_country_if_international(team)][
                    district_year.year
                ].append(team)

            for event in district_events:
                district_yearly_events[district_year.year].append(event)
                region_yearly_events[get_state_or_country_if_international(event)][
                    district_year.year
                ].append(event)

        def make_region_data(
            yearly_teams: Dict[Year, List[Team]], yearly_events: Dict[Year, List[Event]]
        ) -> DistrictInsightDistrictRegionData:
            yearly_gained_teams = {}
            yearly_lost_teams = {}

            for y in yearly_teams.keys():
                y_gain, y_loss = InsightsDistrictsHelper._make_team_deltas(
                    {
                        yr: set([t.key_name for t in teams])
                        for yr, teams in yearly_teams.items()
                    },
                    y - 1,
                    y,
                )
                yearly_gained_teams[y] = y_gain
                yearly_lost_teams[y] = y_loss

            return DistrictInsightDistrictRegionData(
                yearly_active_team_count={
                    y: len(teams) for y, teams in yearly_teams.items()
                },
                yearly_event_count={
                    y: len(events) for y, events in yearly_events.items()
                },
                yearly_gained_teams=yearly_gained_teams,
                yearly_lost_teams=yearly_lost_teams,
            )

        return DistrictInsightDistrictData(
            region_data={
                region: make_region_data(
                    region_yearly_teams[region], region_yearly_events[region]
                )
                for region in region_yearly_teams.keys()
            },
            district_wide_data=make_region_data(
                district_yearly_teams, district_yearly_events
            ),
        )


def get_state_or_country_if_international(team: Team) -> str:
    if team.country not in ["USA", "Canada"]:
        return team.country

    return state_short_code_to_full_name(team.state_prov)


def state_short_code_to_full_name(state_short_code: str) -> str:
    return STATE_ABBREV_TO_NAME.get(state_short_code, state_short_code)
