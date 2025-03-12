import copy
from collections import defaultdict
from typing import (
    cast,
    Dict,
    List,
    NamedTuple,
    Optional,
    Union,
)

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
    OPPONENT,
)
from backend.common.consts.comp_level import (
    COMP_LEVELS_PLAY_ORDER,
    COMP_LEVELS_VERBOSE,
    COMP_LEVELS_VERBOSE_FULL,
    CompLevel,
    ELIM_LEVELS,
)
from backend.common.consts.playoff_type import (
    DoubleElimRound,
    ORDERED_DOUBLE_ELIM_ROUNDS,
    PlayoffType,
)
from backend.common.helpers.match_helper import (
    MatchHelper,
    TOrganizedDoubleElimMatches,
    TOrganizedLegacyDoubleElimMatches,
    TOrganizedMatches,
)
from backend.common.models.alliance import EventAlliance
from backend.common.models.event import Event
from backend.common.models.event_playoff_advancement import (
    ApiPlayoffAdvancement,
    ApiPlayoffAdvancementAllianceRank,
    BracketItem,
    PlayoffAdvancement2015,
    PlayoffAdvancementDoubleElimAlliance,
    PlayoffAdvancementDoubleElimLevels,
    PlayoffAdvancementDoubleElimRound,
    PlayoffAdvancementRoundRobin,
    PlayoffAdvancementRoundRobinLevels,
    TBracketTable,
    TPlayoffAdvancement,
    TPlayoffAdvancement2015Levels,
)
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, TeamNumber, Year
from backend.common.models.match import Match


class PlayoffAdvancement(NamedTuple):
    """
    This is the output of this file's computation
    """

    bracket_table: TBracketTable
    playoff_advancement: Optional[TPlayoffAdvancement]
    double_elim_matches: Optional[
        Union[TOrganizedDoubleElimMatches, TOrganizedLegacyDoubleElimMatches]
    ]
    playoff_template: Optional[str]


class PlayoffAdvancementHelper:
    ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS: Dict[Year, List[str]] = {
        2017: ["totalPoints"],
        2018: ["endgamePoints", "autoPoints"],
        2019: ["cargoPoints", "hatchPanelPoints"],
        2020: [],
        2021: [],
        2022: ["endgamePoints", "autoPoints"],
    }

    ROUND_ROBIN_TIEBREAKERS: Dict[Year, List[str]] = {
        2017: ["Match Points"],
        2018: ["Park/Climb Points", "Auto Points"],
        2019: ["Cargo Points", "Hatch Panel Points"],
        2020: [],
        2021: [],
        2022: ["Hangar Points", "Auto Taxi/Cargo Points"],
    }

    ADVANCEMENT_COUNT_2015: Dict[CompLevel, int] = {
        CompLevel.EF: 8,
        CompLevel.QF: 4,
        CompLevel.SF: 2,
    }

    PLAYOFF_TYPE_TO_TEMPLATE: Dict[PlayoffType, str] = {
        PlayoffType.AVG_SCORE_8_TEAM: "playoff_table",
        PlayoffType.ROUND_ROBIN_6_TEAM: "playoff_round_robin_6_team",
        PlayoffType.CUSTOM: "custom",
    }

    @classmethod
    def playoff_template(cls, event: Event) -> Optional[str]:
        return cls.PLAYOFF_TYPE_TO_TEMPLATE.get(event.playoff_type)

    @classmethod
    def double_elim_matches(
        cls, event: Event, matches: TOrganizedMatches
    ) -> Optional[
        Union[TOrganizedDoubleElimMatches, TOrganizedLegacyDoubleElimMatches]
    ]:
        double_elim_matches = None
        if event.playoff_type == PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM:
            double_elim_matches = MatchHelper.organized_legacy_double_elim_matches(
                matches
            )
        elif event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
            double_elim_matches = MatchHelper.organized_double_elim_matches(
                matches, event.year
            )
        elif event.playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
            double_elim_matches = MatchHelper.organized_double_elim_4_matches(matches)
        return double_elim_matches

    @classmethod
    def generate_playoff_advancement(
        cls, event: Event, matches: TOrganizedMatches
    ) -> PlayoffAdvancement:
        bracket_table = cls._generate_bracket(matches, event, event.alliance_selections)

        playoff_advancement = None

        playoff_template = cls.playoff_template(event)
        double_elim_matches = cls.double_elim_matches(event, matches)

        if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            playoff_advancement = cls.generate_playoff_advancement_2015(
                matches, event.alliance_selections
            )
            for comp_level in [CompLevel.QF, CompLevel.SF]:
                if comp_level in bracket_table:
                    del bracket_table[comp_level]
        elif event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            playoff_advancement = cls.generate_playoff_advancement_round_robin(
                matches, event.year, event.alliance_selections
            )
            comp_levels = list(bracket_table.keys())
            for comp_level in comp_levels:
                if comp_level != CompLevel.F:
                    del bracket_table[comp_level]
        elif event.playoff_type in [
            PlayoffType.DOUBLE_ELIM_4_TEAM,
            PlayoffType.DOUBLE_ELIM_8_TEAM,
        ]:
            playoff_advancement = cls.generate_playoff_advancement_double_elim(
                cast(TOrganizedDoubleElimMatches, double_elim_matches),
                event.alliance_selections,
            )
            # double elim needs the whole bracket, do not remove anything
        elif (
            event.playoff_type == PlayoffType.BO3_FINALS
            or event.playoff_type == PlayoffType.BO5_FINALS
        ):
            comp_levels = list(bracket_table.keys())
            for comp_level in comp_levels:
                if comp_level != CompLevel.F:
                    del bracket_table[comp_level]

        return PlayoffAdvancement(
            bracket_table=bracket_table,
            playoff_advancement=playoff_advancement,
            double_elim_matches=double_elim_matches,
            playoff_template=playoff_template,
        )

    """
    @classmethod
    def generate_playoff_advancement_from_csv(cls, event, csv_advancement, comp_level):
        \"""
        Generate properly formatted advancement info from the output of CSVAdvancementParser
        The output will be of the same format as generate_playoff_advancement_round_robin
        \"""
        if event.playoff_type != PlayoffType.ROUND_ROBIN_6_TEAM:
            return {}

        advancement = []
        for alliance_advancement in csv_advancement:
            alliance = event.alliance_selections[
                alliance_advancement["alliance_number"] - 1
            ]
            advancement.append(
                [
                    list(map(lambda p: int(p[3:]), alliance["picks"])),
                    alliance_advancement["cmp_points_matches"],
                    sum(alliance_advancement["cmp_points_matches"]),
                    alliance_advancement["tiebreak1_matches"],
                    sum(alliance_advancement["tiebreak1_matches"]),
                    alliance_advancement["tiebreak2_matches"],
                    sum(alliance_advancement["tiebreak2_matches"]),
                    alliance.get("name"),
                    {
                        "wins": alliance_advancement["wins"],
                        "losses": alliance_advancement["losses"],
                        "ties": alliance_advancement["ties"],
                    },
                ]
            )

        advancement = sorted(advancement, key=lambda x: -x[6])  # sort by tiebreaker2
        advancement = sorted(advancement, key=lambda x: -x[4])  # sort by tiebreaker1
        advancement = sorted(
            advancement, key=lambda x: -x[2]
        )  # sort by championship points
        return {
            comp_level: advancement,
            "{}_complete".format(comp_level): True,
        }
    """

    @classmethod
    def _generate_bracket(
        cls,
        matches: TOrganizedMatches,
        event: Event,
        alliance_selections: Optional[List[EventAlliance]] = None,
    ) -> TBracketTable:
        complete_alliances = []
        bracket_table = defaultdict(lambda: defaultdict(dict))
        for comp_level in [CompLevel.EF, CompLevel.QF, CompLevel.SF, CompLevel.F]:
            set_numbers = [m.set_number for m in matches[comp_level]]
            for match in matches[comp_level]:
                is_lone_match = set_numbers.count(match.set_number) == 1

                set_key = "{}{}".format(comp_level, match.set_number)
                if set_key not in bracket_table[comp_level]:
                    bracket_table[comp_level][set_key] = {
                        "red_alliance": [],
                        "blue_alliance": [],
                        "winning_alliance": None,
                        "red_wins": 0,
                        "blue_wins": 0,
                        "red_record": {"wins": 0, "losses": 0, "ties": 0},
                        "blue_record": {"wins": 0, "losses": 0, "ties": 0},
                        "red_name": None,
                        "blue_name": None,
                    }
                for color in [AllianceColor.RED, AllianceColor.BLUE]:
                    alliance = copy.copy(match.alliances[color]["teams"])
                    bracket_table[comp_level][set_key][f"{color}_name"] = (
                        cls._alliance_name(alliance, alliance_selections)
                    )
                    for i, complete_alliance in enumerate(
                        complete_alliances
                    ):  # search for alliance. could be more efficient
                        if (
                            len(set(alliance).intersection(set(complete_alliance))) >= 2
                        ):  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(
                                set(alliance).difference(set(complete_alliance))
                            )
                            complete_alliances[
                                i
                            ] += backups  # ensures that backup robots are listed last

                            for team_num in cls.ordered_alliance(
                                complete_alliances[i], alliance_selections
                            ):
                                if (
                                    team_num
                                    not in bracket_table[comp_level][set_key][
                                        f"{color}_alliance"
                                    ]
                                ):
                                    bracket_table[comp_level][set_key][
                                        f"{color}_alliance"
                                    ].append(team_num)

                            break
                    else:
                        complete_alliances.append(alliance)
                        if is_lone_match:
                            bracket_table[comp_level][set_key][
                                f"{color}_alliance"
                            ] += cls.ordered_alliance(alliance, alliance_selections)

                # Skip if match hasn't been played
                if not match.has_been_played:
                    continue

                winner = match.winning_alliance
                if not winner or winner == "":
                    # if the match is a tie
                    bracket_table[comp_level][set_key]["red_record"]["ties"] = (
                        bracket_table[comp_level][set_key]["red_record"]["ties"] + 1
                    )
                    bracket_table[comp_level][set_key]["blue_record"]["ties"] = (
                        bracket_table[comp_level][set_key]["blue_record"]["ties"] + 1
                    )
                    continue

                bracket_table[comp_level][set_key][f"{winner}_wins"] = (
                    bracket_table[comp_level][set_key][f"{winner}_wins"] + 1
                )
                bracket_table[comp_level][set_key][f"{winner}_record"]["wins"] = (
                    bracket_table[comp_level][set_key][f"{winner}_record"]["wins"] + 1
                )

                loser = OPPONENT[winner]
                bracket_table[comp_level][set_key][f"{loser}_record"]["losses"] = (
                    bracket_table[comp_level][set_key][f"{loser}_record"]["losses"] + 1
                )

                n = 2
                if event.playoff_type == PlayoffType.BO5_FINALS:
                    n = 3
                elif event.playoff_type in (
                    PlayoffType.DOUBLE_ELIM_8_TEAM,
                    PlayoffType.DOUBLE_ELIM_4_TEAM,
                ):
                    # only the final is a BO3
                    if not (
                        comp_level == CompLevel.F
                        and match.set_number == set_numbers[-1]
                    ):
                        n = 1
                if bracket_table[comp_level][set_key]["red_wins"] == n:
                    bracket_table[comp_level][set_key][
                        "winning_alliance"
                    ] = AllianceColor.RED
                if bracket_table[comp_level][set_key]["blue_wins"] == n:
                    bracket_table[comp_level][set_key][
                        "winning_alliance"
                    ] = AllianceColor.BLUE

        return bracket_table  # pyre-ignore[7]

    @classmethod
    def generate_playoff_advancement_2015(
        cls,
        matches: TOrganizedMatches,
        alliance_selections: Optional[List[EventAlliance]] = None,
    ) -> TPlayoffAdvancement2015Levels:
        complete_alliances: List[List[TeamNumber]] = []
        alliance_names: List[str] = []
        per_alliance_advancement: defaultdict[
            CompLevel, defaultdict[int, PlayoffAdvancement2015]
        ] = defaultdict(
            lambda: defaultdict(
                lambda: PlayoffAdvancement2015(
                    complete_alliance=[],
                    scores=[],
                    average_score=0,
                    num_played=0,
                )
            )
        )
        advancement: Dict[CompLevel, List[PlayoffAdvancement2015]] = {}

        for comp_level in [CompLevel.EF, CompLevel.QF, CompLevel.SF]:
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    continue

                for color in [AllianceColor.RED, AllianceColor.BLUE]:
                    alliance = cls.ordered_alliance(
                        match.alliances[color]["teams"], alliance_selections
                    )
                    alliance_name: str = (
                        cls._alliance_name(
                            match.alliances[color]["teams"], alliance_selections
                        )
                        or ""
                    )
                    alliance_index = cls._update_complete_alliance(
                        complete_alliances, alliance_names, alliance, alliance_name
                    )

                    (_, scores, _, _) = per_alliance_advancement[comp_level][
                        alliance_index
                    ]
                    scores.append(match.alliances[color]["score"])

                    per_alliance_advancement[comp_level][alliance_index] = (
                        PlayoffAdvancement2015(
                            complete_alliance=complete_alliances[alliance_index],
                            scores=scores,
                            average_score=float(sum(scores)) / len(scores),
                            num_played=len(scores),
                        )
                    )

            sorted_advancements: List[PlayoffAdvancement2015] = list(
                per_alliance_advancement.get(comp_level, {}).values()
            )
            sorted_advancements = sorted(
                sorted_advancements, key=lambda x: -x.average_score
            )  # sort by descending average score
            advancement[comp_level] = sorted_advancements

        return advancement

    @classmethod
    def generate_playoff_advancement_round_robin(
        cls,
        matches: TOrganizedMatches,
        year: Year,
        alliance_selections: Optional[List[EventAlliance]] = None,
    ) -> PlayoffAdvancementRoundRobinLevels:
        complete_alliances: List[List[TeamNumber]] = []
        alliance_names: List[str] = []

        # key is the index into complete_alliances
        per_alliance_advancement: defaultdict[
            CompLevel, defaultdict[int, PlayoffAdvancementRoundRobin]
        ] = defaultdict(
            lambda: defaultdict(
                lambda: PlayoffAdvancementRoundRobin(
                    complete_alliance=[],
                    champ_points=[],
                    sum_champ_points=0,
                    tiebreaker1=[],
                    sum_tiebreaker1=0,
                    tiebreaker2=[],
                    sum_tiebreaker2=0,
                    alliance_name="",
                    record=WLTRecord(wins=0, losses=0, ties=0),
                )
            )
        )

        advancement: Dict[CompLevel, List[PlayoffAdvancementRoundRobin]] = {}
        comp_level = CompLevel.SF
        any_unplayed = False
        for match in matches.get(comp_level, []):
            if not match.has_been_played:
                any_unplayed = True
            for color in [AllianceColor.RED, AllianceColor.BLUE]:
                alliance = cls.ordered_alliance(
                    match.alliances[color]["teams"], alliance_selections
                )
                alliance_name: str = (
                    cls._alliance_name(
                        match.alliances[color]["teams"], alliance_selections
                    )
                    or ""
                )

                i = cls._update_complete_alliance(
                    complete_alliances, alliance_names, alliance, alliance_name
                )

                (
                    _,
                    champ_points,
                    _,
                    tiebreaker1,
                    _,
                    tiebreaker2,
                    _,
                    _,
                    record,
                ) = per_alliance_advancement[comp_level][i]
                cls.update_wlt(match, color, record)
                cp = cls.round_robin_champ_points_earned(match, color)
                if match.has_been_played:
                    champ_points.append(cp)

                    if (
                        year in cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS
                        and match.score_breakdown is not None
                    ):
                        breakdown = none_throws(match.score_breakdown)
                        tiebreak_keys = cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS[year]

                        key1 = tiebreak_keys[0] if len(tiebreak_keys) > 0 else None
                        tiebreaker1.append(breakdown[color][key1] if key1 else 0)

                        key2 = tiebreak_keys[1] if len(tiebreak_keys) > 1 else None
                        tiebreaker2.append(breakdown[color][key2] if key2 else 0)

                per_alliance_advancement[comp_level][i] = PlayoffAdvancementRoundRobin(
                    complete_alliance=complete_alliances[i],
                    alliance_name=alliance_names[i],
                    champ_points=champ_points,
                    sum_champ_points=sum(champ_points),
                    tiebreaker1=tiebreaker1,
                    sum_tiebreaker1=sum(tiebreaker1),
                    tiebreaker2=tiebreaker2,
                    sum_tiebreaker2=sum(tiebreaker2),
                    record=record,
                )

        alliance_advancements: List[PlayoffAdvancementRoundRobin] = list(
            per_alliance_advancement[comp_level].values()
        )
        alliance_advancements = sorted(
            alliance_advancements, key=lambda x: -x.sum_tiebreaker2
        )  # sort by tiebreaker2
        alliance_advancements = sorted(
            alliance_advancements, key=lambda x: -x.sum_tiebreaker1
        )  # sort by tiebreaker1
        alliance_advancements = sorted(
            alliance_advancements, key=lambda x: -x.sum_champ_points
        )  # sort by championship points
        advancement[comp_level] = alliance_advancements

        return PlayoffAdvancementRoundRobinLevels(
            sf=advancement[CompLevel.SF],
            sf_complete=(not any_unplayed),
        )

    @classmethod
    def round_robin_champ_points_earned(cls, match: Match, color: AllianceColor) -> int:
        if not match.has_been_played:
            return 0
        elif match.winning_alliance == color:
            return 2
        elif match.winning_alliance == "":
            return 1
        else:
            return 0

    @classmethod
    def generate_playoff_advancement_double_elim(
        cls,
        organized_matches: TOrganizedDoubleElimMatches,
        alliance_selections: Optional[List[EventAlliance]] = None,
    ) -> PlayoffAdvancementDoubleElimLevels:
        rounds: defaultdict[DoubleElimRound, PlayoffAdvancementDoubleElimRound] = (
            defaultdict(
                lambda: PlayoffAdvancementDoubleElimRound(
                    competing_alliances=[],
                    complete=False,
                )
            )
        )

        complete_alliances: List[List[TeamNumber]] = []
        alliance_names: List[str] = []

        # key is the index into "complete_alliances"
        cumulative_record_per_alliance: defaultdict[int, WLTRecord] = defaultdict(
            lambda: WLTRecord(wins=0, losses=0, ties=0)
        )
        per_round_record_per_alliance: defaultdict[
            DoubleElimRound, defaultdict[int, WLTRecord]
        ] = defaultdict(
            lambda: defaultdict(lambda: WLTRecord(wins=0, losses=0, ties=0))
        )

        for round in ORDERED_DOUBLE_ELIM_ROUNDS:
            matches = organized_matches.get(round)
            if not matches:
                continue

            round_alliances: List[PlayoffAdvancementDoubleElimAlliance] = []
            any_unplayed = False
            for match in matches:
                if not match.has_been_played:
                    any_unplayed = True

                for color in [AllianceColor.RED, AllianceColor.BLUE]:
                    alliance = cls.ordered_alliance(
                        match.alliances[color]["teams"], alliance_selections
                    )
                    alliance_name: str = (
                        cls._alliance_name(
                            match.alliances[color]["teams"], alliance_selections
                        )
                        or ""
                    )

                    alliance_index = cls._update_complete_alliance(
                        complete_alliances, alliance_names, alliance, alliance_name
                    )

                    cls.update_wlt(
                        match,
                        color,
                        per_round_record_per_alliance[round][alliance_index],
                    )
                    cls.update_wlt(
                        match, color, cumulative_record_per_alliance[alliance_index]
                    )

                    round_alliances.append(
                        PlayoffAdvancementDoubleElimAlliance(
                            complete_alliance=complete_alliances[alliance_index],
                            alliance_name=alliance_names[alliance_index],
                            record=per_round_record_per_alliance[round][alliance_index],
                            eliminated=(
                                cumulative_record_per_alliance[alliance_index]["losses"]
                                >= 2
                            ),
                        )
                    )

            rounds[round] = PlayoffAdvancementDoubleElimRound(
                competing_alliances=round_alliances,
                complete=(not any_unplayed),
            )

        return PlayoffAdvancementDoubleElimLevels(
            rounds=rounds,
        )

    @classmethod
    def ordered_alliance(
        cls,
        team_keys: List[TeamKey],
        alliance_selections: Optional[List[EventAlliance]],
    ) -> List[TeamNumber]:
        if alliance_selections:
            for (
                alliance_selection
            ) in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection["picks"]
                if (
                    len(set(picks).intersection(set(team_keys))) >= 2
                ):  # if >= 2 teams are the same, then the alliance is the same
                    backups = list(set(team_keys).difference(set(picks)))
                    team_keys = picks + backups
                    break

        team_nums = []
        for team in team_keys:
            # Strip the "frc" prefix
            team_nums.append(team[3:])
        return team_nums

    @classmethod
    def update_wlt(cls, match: Match, color: AllianceColor, record: WLTRecord) -> None:
        if match.has_been_played:
            if match.winning_alliance == "":
                record["ties"] += 1
            elif match.winning_alliance == color:
                record["wins"] += 1
            elif match.winning_alliance != color:
                record["losses"] += 1

    @classmethod
    def _alliance_name(
        cls,
        team_keys: List[TeamKey],
        alliance_selections: Optional[List[EventAlliance]],
    ) -> Optional[str]:
        if not alliance_selections:
            return None
        for n, alliance_selection in enumerate(
            alliance_selections
        ):  # search for alliance. could be more efficient
            picks = alliance_selection["picks"]
            if (
                len(set(picks).intersection(set(team_keys))) >= 2
            ):  # if >= 2 teams are the same, then the alliance is the same
                return alliance_selection.get("name", f"Alliance {n + 1}")
        return None

    @classmethod
    def _update_complete_alliance(
        cls,
        complete_alliances: List[List[TeamNumber]],
        alliance_names: List[str],
        alliance: List[TeamNumber],
        alliance_name: str,
    ) -> int:
        # return alliance_index
        for i, complete_alliance in enumerate(
            complete_alliances
        ):  # search for alliance. could be more efficient
            if (
                len(set(alliance).intersection(set(complete_alliance))) >= 2
            ):  # if >= 2 teams are the same, then the alliance is the same
                backups = list(set(alliance).difference(set(complete_alliance)))
                complete_alliances[
                    i
                ] += backups  # ensures that backup robots are listed last
                alliance_names[i] = alliance_name
                return i

        complete_alliances.append(alliance)
        alliance_names.append(alliance_name)
        return len(complete_alliances) - 1

    @classmethod
    def create_playoff_advancement_response_for_apiv3(
        cls,
        event: Event,
        playoff_advancement: Optional[TPlayoffAdvancement],
        bracket_table: TBracketTable,
    ) -> List[ApiPlayoffAdvancement]:
        output: List[ApiPlayoffAdvancement] = []

        if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            bracket_levels_to_include = [CompLevel.F]
            advancement2015 = cast(TPlayoffAdvancement2015Levels, playoff_advancement)
            for level in ELIM_LEVELS:
                if not advancement2015.get(level):
                    continue
                output.extend(
                    cls.transform_2015_advancement_level_for_apiv3(
                        event,
                        advancement2015,
                        level,
                    )
                )
        elif event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            bracket_levels_to_include = [CompLevel.F]
            output.extend(
                cls.transform_round_robin_advancement_level_for_apiv3(
                    event,
                    cast(PlayoffAdvancementRoundRobinLevels, playoff_advancement),
                )
            )
        elif event.playoff_type in [
            PlayoffType.DOUBLE_ELIM_4_TEAM,
            PlayoffType.DOUBLE_ELIM_8_TEAM,
        ]:
            bracket_levels_to_include = [CompLevel.F]
            double_elim_advancement = cast(
                PlayoffAdvancementDoubleElimLevels, playoff_advancement
            )
            for round in ORDERED_DOUBLE_ELIM_ROUNDS:
                if round not in double_elim_advancement["rounds"]:
                    continue

                output.extend(
                    cls.transform_double_elim_advancement_level_for_apiv3(
                        event,
                        double_elim_advancement,
                        round,
                    )
                )
        else:
            bracket_levels_to_include = ELIM_LEVELS

        for level in bracket_levels_to_include:
            if not bracket_table.get(level):
                continue

            level_ranks: List[ApiPlayoffAdvancement] = []
            level_ranks = PlayoffAdvancementHelper.transform_bracket_level_for_apiv3(
                event, bracket_table, level
            )
            output.extend(level_ranks)
        return output

    @classmethod
    def transform_bracket_level_for_apiv3(
        cls, event: Event, bracket_table: TBracketTable, comp_level: CompLevel
    ) -> List[ApiPlayoffAdvancement]:
        level_ranks = []
        for series_level, set_bracket in bracket_table[comp_level].items():
            series = int("".join(c for c in series_level if c.isdigit()))
            data = {
                "level": "{}{}".format(comp_level, series),
                "level_name": COMP_LEVELS_VERBOSE_FULL[comp_level]
                + (" %d" % series if comp_level != "f" else ""),
                "rankings": None,
                "type": "best_of_3",
                "sort_order_info": [{"name": "Wins", "type": "int", "precision": 0}],
                "extra_stats_info": [],
            }

            alliances = [
                cls._make_alliance_rank_row_for_apiv3(c, set_bracket)
                for c in ALLIANCE_COLORS
            ]
            data["rankings"] = sorted(
                alliances, key=lambda a: a["record"]["wins"], reverse=True
            )

            level_ranks.append(data)

        return level_ranks

    @classmethod
    def _make_alliance_rank_row_for_apiv3(
        cls, color: AllianceColor, bracket_set: BracketItem
    ) -> ApiPlayoffAdvancementAllianceRank:
        record: WLTRecord = bracket_set["{}_record".format(color)]  # pyre-ignore[26, 9]
        return ApiPlayoffAdvancementAllianceRank(
            team_keys=list(
                map(
                    lambda t: "frc{}".format(t),
                    bracket_set["{}_alliance".format(color)],  # pyre-ignore[26]
                )
            ),
            alliance_name=bracket_set["{}_name".format(color)],  # pyre-ignore[26, 6]
            alliance_color=color,
            record=record,
            matches_played=record["wins"] + record["losses"] + record["ties"],
            sort_orders=[bracket_set["{}_wins".format(color)]],  # pyre-ignore[26]
            extra_stats=[],
        )

    @classmethod
    def transform_2015_advancement_level_for_apiv3(
        cls,
        event: Event,
        playoff_advancement: TPlayoffAdvancement2015Levels,
        comp_level: CompLevel,
    ) -> List[ApiPlayoffAdvancement]:
        level_order = COMP_LEVELS_PLAY_ORDER[comp_level]
        next_level = list(COMP_LEVELS_PLAY_ORDER.keys())[
            list(COMP_LEVELS_PLAY_ORDER.values()).index(level_order + 1)
        ]
        data = ApiPlayoffAdvancement(
            level=comp_level,
            level_name=COMP_LEVELS_VERBOSE_FULL[comp_level],
            rankings=[],
            type="average_score",
            sort_order_info=[
                {"name": "Average Score", "type": "int", "precision": 2},
            ],
            extra_stats_info=[
                {
                    "name": "Advance to {}".format(COMP_LEVELS_VERBOSE[next_level]),
                    "type": "bool",
                    "precision": 0,
                },
            ],
        )
        for i, alliance in enumerate(playoff_advancement[comp_level]):
            rank = i + 1
            none_throws(data["rankings"]).append(
                cls._make_2015_alliance_advancement_row_for_apiv3(
                    event, alliance, rank, comp_level
                )
            )
        return [data]

    @classmethod
    def transform_round_robin_advancement_level_for_apiv3(
        cls,
        event: Event,
        playoff_advancement: PlayoffAdvancementRoundRobinLevels,
    ) -> List[ApiPlayoffAdvancement]:
        data = ApiPlayoffAdvancement(
            level=str(CompLevel.SF),
            level_name="Round Robin " + COMP_LEVELS_VERBOSE_FULL[CompLevel.SF],
            rankings=[],
            type="round_robin",
            sort_order_info=[
                {"name": "Champ Points", "type": "int", "precision": 0},
            ],
            extra_stats_info=[
                {"name": "Advance to Finals", "type": "bool", "precision": 0},
            ],
        )

        for tiebreaker in cls.ROUND_ROBIN_TIEBREAKERS[event.year]:
            data["sort_order_info"].append(
                {"name": tiebreaker, "type": "int", "precision": 0}
            )

        for i, alliance in enumerate(playoff_advancement["sf"]):
            rank = i + 1
            none_throws(data["rankings"]).append(
                cls._make_round_robin_alliance_advancement_row_for_apiv3(
                    event, alliance, rank
                )
            )
        return [data]

    @classmethod
    def transform_double_elim_advancement_level_for_apiv3(
        cls,
        event: Event,
        playoff_advancement: PlayoffAdvancementDoubleElimLevels,
        round: DoubleElimRound,
    ) -> List[ApiPlayoffAdvancement]:
        data = ApiPlayoffAdvancement(
            level=round.name.lower(),
            level_name=round.value,
            rankings=[],
            type="double_elim",
            sort_order_info=[],
            extra_stats_info=[
                {"name": "Eliminated", "type": "bool", "precision": 0},
            ],
        )

        for alliance in playoff_advancement["rounds"][round][0]:
            none_throws(data["rankings"]).append(
                cls._make_double_elim_alliance_advancement_row_for_apiv3(alliance)
            )

        return [data]

    @classmethod
    def _make_round_robin_alliance_advancement_row_for_apiv3(
        cls, event: Event, alliance: PlayoffAdvancementRoundRobin, rank: int
    ) -> ApiPlayoffAdvancementAllianceRank:
        record = alliance[8]
        row = ApiPlayoffAdvancementAllianceRank(
            team_keys=list(map(lambda t: "frc{}".format(t), alliance[0])),
            alliance_name=alliance[7],  # alliance name
            record=record,
            matches_played=record["wins"] + record["losses"] + record["ties"],
            rank=rank,
            sort_orders=[alliance[2], alliance[4], alliance[6]],
            extra_stats=[int(rank <= 2)],  # top 2 teams advance
        )

        return row

    @classmethod
    def _make_2015_alliance_advancement_row_for_apiv3(
        cls,
        event: Event,
        alliance: PlayoffAdvancement2015,
        rank: int,
        comp_level: CompLevel,
    ) -> ApiPlayoffAdvancementAllianceRank:
        team_keys = list(map(lambda t: "frc{}".format(t), alliance[0]))
        row = ApiPlayoffAdvancementAllianceRank(
            team_keys=team_keys,
            alliance_name=none_throws(
                cls._alliance_name(team_keys, event.alliance_selections)
            ),
            rank=rank,
            matches_played=alliance[3],
            sort_orders=[alliance[2]],
            extra_stats=[int(rank <= cls.ADVANCEMENT_COUNT_2015[comp_level])],
        )

        return row

    @classmethod
    def _make_double_elim_alliance_advancement_row_for_apiv3(
        cls, alliance: PlayoffAdvancementDoubleElimAlliance
    ) -> ApiPlayoffAdvancementAllianceRank:
        return ApiPlayoffAdvancementAllianceRank(
            team_keys=list(
                map(lambda t: "frc{}".format(t), alliance["complete_alliance"])
            ),
            alliance_name=alliance["alliance_name"],
            record=alliance["record"],
            matches_played=alliance["record"]["wins"]
            + alliance["record"]["losses"]
            + alliance["record"]["ties"],
            sort_orders=[],
            extra_stats=[
                int(alliance["eliminated"]),
            ],
        )
