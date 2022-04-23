import copy
from collections import defaultdict
from typing import (
    Any,
    cast,
    DefaultDict,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    TypedDict,
)

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor, OPPONENT, TMatchWinner
from backend.common.consts.comp_level import (
    COMP_LEVELS_PLAY_ORDER,
    COMP_LEVELS_VERBOSE,
    COMP_LEVELS_VERBOSE_FULL,
    CompLevel,
    ELIM_LEVELS,
)
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.match_helper import (
    MatchHelper,
    TOrganizedDoubleElimMatches,
    TOrganizedMatches,
)
from backend.common.models.alliance import EventAlliance
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, TeamNumber, Year


class PlayoffAdvancement(NamedTuple):
    """
    This is the output of this file's computation
    """

    bracket_table: Any
    playoff_advancement: Any
    double_elim_matches: Optional[TOrganizedDoubleElimMatches]
    playoff_template: Optional[str]


class PlayoffAdvancement2015(NamedTuple):
    complete_alliance: List[TeamNumber]
    scores: List[int]
    average_score: float
    num_played: int


class PlayoffAdvancementRoundRobin(NamedTuple):
    complete_alliance: List[TeamNumber]
    champ_points: List[int]
    sum_champ_points: int
    tiebreaker1: List[int]
    sum_tiebreaker1: int
    tiebreaker2: List[int]
    sum_tiebreaker2: int
    alliance_name: str
    record: WLTRecord


class PlayoffAdvancementRoundRobinLevels(TypedDict):
    sf: List[PlayoffAdvancementRoundRobin]
    sf_complete: bool


class BracketItem(TypedDict):
    red_alliance: List[TeamNumber]
    blue_alliance: List[TeamNumber]
    winning_alliance: Optional[TMatchWinner]
    red_wins: int
    blue_wins: int
    red_record: WLTRecord
    blue_record: WLTRecord
    red_name: Optional[str]
    blue_name: Optional[str]


class PlayoffAdvancementHelper(object):

    ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS: Dict[Year, List[str]] = {
        2017: ["score"],
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
    ) -> Optional[TOrganizedDoubleElimMatches]:
        double_elim_matches = None
        if event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
            double_elim_matches = MatchHelper.organized_double_elim_matches(matches)
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
        elif (
            event.playoff_type == PlayoffType.BO3_FINALS
            or event.playoff_type == PlayoffType.BO5_FINALS
        ):
            comp_levels = list(bracket_table.keys())
            for comp_level in comp_levels:
                if comp_level != CompLevel.F:
                    del bracket_table[comp_level]

        return PlayoffAdvancement(
            bracket_table,
            playoff_advancement,
            double_elim_matches,
            playoff_template,
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
    ) -> Mapping[CompLevel, Mapping[str, BracketItem]]:
        complete_alliances = []
        bracket_table = defaultdict(lambda: defaultdict(dict))
        for comp_level in [CompLevel.QF, CompLevel.SF, CompLevel.F]:
            for match in matches[comp_level]:
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
                    bracket_table[comp_level][set_key][
                        f"{color}_name"
                    ] = cls._alliance_name(alliance, alliance_selections)
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

                loser = OPPONENT[cast(AllianceColor, winner)]
                bracket_table[comp_level][set_key][f"{loser}_record"]["losses"] = (
                    bracket_table[comp_level][set_key][f"{loser}_record"]["losses"] + 1
                )

                n = 3 if event.playoff_type == PlayoffType.BO5_FINALS else 2
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
    ) -> Mapping[CompLevel, List[PlayoffAdvancement2015]]:
        complete_alliances: List[List[TeamNumber]] = []
        advancement: DefaultDict[CompLevel, List[PlayoffAdvancement2015]] = defaultdict(
            list
        )  # key: comp level; value: list of [complete_alliance, [scores], average_score, num_played]
        for comp_level in [CompLevel.EF, CompLevel.QF, CompLevel.SF]:
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    continue
                for color in [AllianceColor.RED, AllianceColor.BLUE]:
                    alliance = cls.ordered_alliance(
                        match.alliances[color]["teams"], alliance_selections
                    )
                    alliance_index = None
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
                            alliance_index = i
                            break
                    else:
                        complete_alliances.append(alliance)

                    is_new = False
                    if alliance_index is not None:
                        for j, (complete_alliance, scores, _, _) in enumerate(
                            advancement[comp_level]
                        ):  # search for alliance. could be more efficient
                            if (
                                len(
                                    set(
                                        complete_alliances[alliance_index]
                                    ).intersection(set(complete_alliance))
                                )
                                >= 2
                            ):  # if >= 2 teams are the same, then the alliance is the same
                                complete_alliance = complete_alliances[alliance_index]
                                scores.append(match.alliances[color]["score"])
                                advancement[comp_level][j] = advancement[comp_level][
                                    j
                                ]._replace(
                                    scores=scores,
                                    average_score=float(sum(scores)) / len(scores),
                                    num_played=len(scores),
                                )
                                break
                        else:
                            is_new = True

                    score = match.alliances[color]["score"]
                    if alliance_index is None:
                        advancement[comp_level].append(
                            PlayoffAdvancement2015(alliance, [score], score, 1)
                        )
                    elif is_new:
                        advancement[comp_level].append(
                            PlayoffAdvancement2015(
                                complete_alliances[alliance_index], [score], score, 1
                            )
                        )

            advancement[comp_level] = sorted(
                advancement[comp_level], key=lambda x: -x.average_score
            )  # sort by descending average score

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
        advancement: DefaultDict[
            CompLevel, List[PlayoffAdvancementRoundRobin]
        ] = defaultdict(
            list
        )  # key: comp level; value: list of [complete_alliance, [champ_points], sum_champ_points, [tiebreaker1], sum_tiebreaker1, [tiebreaker2], sum_tiebreaker2
        for comp_level in [CompLevel.SF]:  # In case this needs to scale to more levels
            any_unplayed = False
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    any_unplayed = True
                for color in [AllianceColor.RED, AllianceColor.BLUE]:
                    alliance = cls.ordered_alliance(
                        match.alliances[color]["teams"], alliance_selections
                    )
                    alliance_name: str = (
                        cls.alliance_name(
                            match.alliances[color]["teams"], alliance_selections
                        )
                        or ""
                    )
                    i: Optional[int] = None
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
                            alliance_names[i] = alliance_name
                            break
                    else:
                        i = None
                        complete_alliances.append(alliance)
                        alliance_names.append(alliance_name)

                    is_new = False
                    if i is not None:
                        for (
                            j,
                            (
                                complete_alliance,
                                champ_points,
                                _,
                                tiebreaker1,
                                _,
                                tiebreaker2,
                                _,
                                _,
                                record,
                            ),
                        ) in enumerate(
                            advancement[comp_level]
                        ):  # search for alliance. could be more efficient
                            if (
                                len(
                                    set(complete_alliances[i]).intersection(
                                        set(complete_alliance)
                                    )
                                )
                                >= 2
                            ):  # if >= 2 teams are the same, then the alliance is the same
                                if not match.has_been_played:
                                    cp = 0
                                elif match.winning_alliance == color:
                                    cp = 2
                                    record["wins"] += 1
                                elif match.winning_alliance == "":
                                    cp = 1
                                    record["ties"] += 1
                                else:
                                    cp = 0
                                    record["losses"] += 1
                                if match.has_been_played:
                                    champ_points.append(cp)

                                    if (
                                        year in cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS
                                        and match.score_breakdown is not None
                                    ):
                                        breakdown = none_throws(match.score_breakdown)
                                        tiebreak_keys = (
                                            cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS[year]
                                        )

                                        key1 = (
                                            tiebreak_keys[0]
                                            if len(tiebreak_keys) > 0
                                            else None
                                        )
                                        tiebreaker1.append(
                                            breakdown[color][key1] if key1 else 0
                                        )

                                        key2 = (
                                            tiebreak_keys[1]
                                            if len(tiebreak_keys) > 1
                                            else None
                                        )
                                        tiebreaker2.append(
                                            breakdown[color][key2] if key2 else 0
                                        )

                                    advancement[comp_level][j] = advancement[
                                        comp_level
                                    ][j]._replace(
                                        champ_points=champ_points,
                                        sum_champ_points=sum(champ_points),
                                        tiebreaker1=tiebreaker1,
                                        sum_tiebreaker1=sum(tiebreaker1),
                                        tiebreaker2=tiebreaker2,
                                        sum_tiebreaker2=sum(tiebreaker2),
                                        record=record,
                                    )
                                break
                        else:
                            is_new = True

                    if (
                        year in cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS
                        and match.score_breakdown is not None
                    ):
                        breakdown = none_throws(match.score_breakdown)
                        tiebreak_keys = cls.ROUND_ROBIN_TIEBREAK_BEAKDOWN_KEYS[year]

                        key1 = tiebreak_keys[0] if len(tiebreak_keys) > 0 else None
                        tiebreaker1 = (
                            breakdown[color][key1]
                            if key1 and match.has_been_played
                            else 0
                        )

                        key2 = tiebreak_keys[1] if len(tiebreak_keys) > 1 else None
                        tiebreaker2 = (
                            breakdown[color][key2]
                            if key2 and match.has_been_played
                            else 0
                        )
                    else:
                        tiebreaker1 = 0
                        tiebreaker2 = 0

                    record: WLTRecord = {"wins": 0, "losses": 0, "ties": 0}
                    if not match.has_been_played:
                        cp = 0
                    elif match.winning_alliance == color:
                        cp = 2
                        record["wins"] += 1
                    elif match.winning_alliance == "":
                        cp = 1
                        record["ties"] += 1
                    else:
                        cp = 0
                        record["losses"] += 1
                    if i is None:
                        advancement[comp_level].append(
                            PlayoffAdvancementRoundRobin(
                                alliance,
                                [cp],
                                cp,
                                [tiebreaker1],
                                tiebreaker1,
                                [tiebreaker2],
                                tiebreaker2,
                                alliance_name,
                                record,
                            )
                        )
                    elif is_new:
                        advancement[comp_level].append(
                            PlayoffAdvancementRoundRobin(
                                complete_alliances[i],
                                [cp],
                                cp,
                                [tiebreaker1],
                                tiebreaker1,
                                [tiebreaker2],
                                tiebreaker2,
                                alliance_names[i],
                                record,
                            )
                        )

            advancement[comp_level] = sorted(
                advancement[comp_level], key=lambda x: -x.sum_tiebreaker2
            )  # sort by tiebreaker2
            advancement[comp_level] = sorted(
                advancement[comp_level], key=lambda x: -x.sum_tiebreaker1
            )  # sort by tiebreaker1
            advancement[comp_level] = sorted(
                advancement[comp_level], key=lambda x: -x.sum_champ_points
            )  # sort by championship points

            advancement[
                "{}_complete".format(comp_level)  # pyre-ignore
            ] = not any_unplayed  # pyre-ignore[6]

        return cast(PlayoffAdvancementRoundRobinLevels, advancement)

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
    def _alliance_name(
        cls,
        team_keys: List[TeamKey],
        alliance_selections: Optional[List[EventAlliance]],
    ) -> Optional[str]:
        if not alliance_selections:
            return None
        for (
            alliance_selection
        ) in alliance_selections:  # search for alliance. could be more efficient
            picks = alliance_selection["picks"]
            if (
                len(set(picks).intersection(set(team_keys))) >= 2
            ):  # if >= 2 teams are the same, then the alliance is the same
                return alliance_selection.get("name")
        return None

    @classmethod
    def alliance_name(
        cls,
        team_keys: List[TeamKey],
        alliance_selections: Optional[List[EventAlliance]],
    ) -> Optional[str]:
        if alliance_selections:
            for (
                alliance_selection
            ) in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection["picks"]
                if (
                    len(set(picks).intersection(set(team_keys))) >= 2
                ):  # if >= 2 teams are the same, then the alliance is the same
                    return alliance_selection.get("name")

        return ""

    @classmethod
    def create_playoff_advancement_response_for_apiv3(
        cls, event, playoff_advancement, bracket_table
    ):
        output = []
        for level in ELIM_LEVELS:
            level_ranks = []
            if playoff_advancement and playoff_advancement.get(level):
                if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
                    level_ranks = PlayoffAdvancementHelper.transform_2015_advancement_level_for_apiv3(
                        event, playoff_advancement, level
                    )
                else:
                    level_ranks = PlayoffAdvancementHelper.transform_round_robin_advancement_level_for_apiv3(
                        event, playoff_advancement, level
                    )
            elif bracket_table and bracket_table.get(level):
                level_ranks = (
                    PlayoffAdvancementHelper.transform_bracket_level_for_apiv3(
                        event, bracket_table, level
                    )
                )
            output.extend(level_ranks)
        return output

    @classmethod
    def transform_bracket_level_for_apiv3(cls, event, bracket_table, comp_level):
        level_ranks = []
        for series_level, set_bracket in bracket_table[comp_level].items():
            series = int("".join(c for c in series_level if c.isdigit()))
            data = {
                "level": "{}{}".format(comp_level, series),
                "level_name": COMP_LEVELS_VERBOSE_FULL[comp_level]
                + (" %d" % series if comp_level != "f" else ""),
                "rankings": None,
                "type": "best_of_3",  # TODO handle other playoff types
                "sort_order_info": [{"name": "Wins", "type": "int", "precision": 0}],
                "extra_stats_info": [],
            }

            alliances = [
                cls._make_alliance_rank_row_for_apiv3(c, set_bracket)
                for c in ["red", "blue"]
            ]
            data["rankings"] = sorted(
                alliances, key=lambda a: a["record"]["wins"], reverse=True
            )

            level_ranks.append(data)

        return level_ranks

    @classmethod
    def _make_alliance_rank_row_for_apiv3(cls, color, bracket_set):
        record = bracket_set["{}_record".format(color)]
        return {
            "team_keys": list(
                map(
                    lambda t: "frc{}".format(t),
                    bracket_set["{}_alliance".format(color)],
                )
            ),
            "alliance_name": bracket_set["{}_name".format(color)],
            "alliance_color": color,
            "record": record,
            "matches_played": record["wins"] + record["losses"] + record["ties"],
            "sort_orders": [bracket_set["{}_wins".format(color)]],
            "extra_stats": [],
        }

    @classmethod
    def transform_2015_advancement_level_for_apiv3(
        cls, event, playoff_advancement, comp_level
    ):
        level_order = COMP_LEVELS_PLAY_ORDER[comp_level]
        next_level = list(COMP_LEVELS_PLAY_ORDER.keys())[
            list(COMP_LEVELS_PLAY_ORDER.values()).index(level_order + 1)
        ]
        data = {
            "level": comp_level,
            "level_name": COMP_LEVELS_VERBOSE_FULL[comp_level],
            "rankings": [],
            "type": "average_score",
            "sort_order_info": [
                {"name": "Average Score", "type": "int", "precision": 2},
            ],
            "extra_stats_info": [
                {
                    "name": "Advance to {}".format(COMP_LEVELS_VERBOSE[next_level]),
                    "type": "bool",
                    "precision": 0,
                },
            ],
        }
        for i, alliance in enumerate(playoff_advancement[comp_level]):
            rank = i + 1
            data["rankings"].append(
                cls._make_2015_alliance_advancement_row_for_apiv3(
                    event, alliance, rank, comp_level
                )
            )
        return [data]

    @classmethod
    def transform_round_robin_advancement_level_for_apiv3(
        cls, event, playoff_advancement, comp_level
    ):
        data = {
            "level": comp_level,
            "level_name": "Round Robin " + COMP_LEVELS_VERBOSE_FULL[comp_level],
            "rankings": [],
            "type": "round_robin",
            "sort_order_info": [
                {"name": "Champ Points", "type": "int", "precision": 0},
            ],
            "extra_stats_info": [
                {"name": "Advance to Finals", "type": "bool", "precision": 0},
            ],
        }

        for tiebreaker in cls.ROUND_ROBIN_TIEBREAKERS[event.year]:
            data["sort_order_info"].append(
                {"name": tiebreaker, "type": "int", "precision": 0}
            )

        for i, alliance in enumerate(playoff_advancement[comp_level]):
            rank = i + 1
            data["rankings"].append(
                cls._make_alliance_advancement_row_for_apiv3(event, alliance, rank)
            )
        return [data]

    @classmethod
    def _make_alliance_advancement_row_for_apiv3(cls, event, alliance, rank):
        record = alliance[8]
        row = {
            "team_keys": list(map(lambda t: "frc{}".format(t), alliance[0])),
            "alliance_name": alliance[7],  # alliance name
            "record": record,
            "matches_played": record["wins"] + record["losses"] + record["ties"],
            "rank": rank,
            "sort_orders": [alliance[2], alliance[4], alliance[6]],
            "extra_stats": [int(rank <= 2)],  # top 2 teams advance
        }

        return row

    @classmethod
    def _make_2015_alliance_advancement_row_for_apiv3(
        cls, event, alliance, rank, comp_level
    ):
        team_keys = list(map(lambda t: "frc{}".format(t), alliance[0]))
        row = {
            "team_keys": team_keys,
            "alliance_name": cls._alliance_name(team_keys, event.alliance_selections),
            "rank": rank,
            "matches_played": alliance[3],
            "sort_orders": [alliance[2]],
            "extra_stats": [int(rank <= cls.ADVANCEMENT_COUNT_2015[comp_level])],
        }

        return row
