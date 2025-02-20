from typing import Dict, List, Optional, Tuple

from pyre_extensions import none_throws

from backend.common.consts.comp_level import COMP_LEVELS_VERBOSE_FULL, CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import DoubleElimRound, PlayoffType
from backend.common.models.alliance import (
    EventAlliance,
    PlayoffAllianceStatus,
    PlayoffOutcome,
)
from backend.common.models.event import Event
from backend.common.models.keys import TeamKey


class AllianceHelper:
    UNKNOWN_ALLIANCE_SIZE = 99

    KNOWN_MODERN_EVENT_TYPE_ALLIANCE_SIZES: Dict[EventType, int] = {
        EventType.REGIONAL: 3,
        EventType.DISTRICT: 3,
        EventType.DISTRICT_CMP: 3,
        EventType.DISTRICT_CMP_DIVISION: 3,
        EventType.CMP_DIVISION: 4,
        EventType.CMP_FINALS: 4,
    }

    @classmethod
    def get_known_alliance_size(
        cls,
        event_type: EventType,
        year: int,
    ) -> int:

        if year < 2014:
            # 2014 was first year of 4 team champs divisions
            # for now, return default for legacy events
            return cls.UNKNOWN_ALLIANCE_SIZE

        return cls.KNOWN_MODERN_EVENT_TYPE_ALLIANCE_SIZES.get(
            event_type, cls.UNKNOWN_ALLIANCE_SIZE
        )

    @staticmethod
    def get_ordinal_pick_from_number(n: int) -> str:
        # https://stackoverflow.com/a/20007730
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        return f"{n}{suffix} Pick"

    @classmethod
    def get_alliance_details_and_pick_name(
        cls, event: Event, team: TeamKey
    ) -> Tuple[Optional[EventAlliance], Optional[str], int]:
        alliance_size = cls.get_known_alliance_size(event.event_type_enum, event.year)

        if event.alliance_selections is None:
            return (None, None, alliance_size)

        for alliance in none_throws(event.alliance_selections):
            if team in alliance["picks"]:
                if team == alliance["picks"][0]:
                    return (alliance, "Captain", alliance_size)
                else:
                    index = alliance["picks"].index(team)
                    if index >= alliance_size:
                        return (alliance, "Backup", alliance_size)
                    else:
                        return (
                            alliance,
                            cls.get_ordinal_pick_from_number(index),
                            alliance_size,
                        )

            if (
                "backup" in alliance
                and alliance["backup"]
                and alliance["backup"]["in"] == team
            ):
                return (alliance, "Backup", alliance_size)

        return (None, None, alliance_size)

    @classmethod
    def generate_playoff_level_status_string(
        cls,
        playoff_type: Optional[PlayoffType],
        playoff_status: PlayoffAllianceStatus,
    ) -> str:
        if playoff_type in [
            PlayoffType.DOUBLE_ELIM_4_TEAM,
            PlayoffType.DOUBLE_ELIM_8_TEAM,
        ]:
            double_elim_round = playoff_status["double_elim_round"]
            if double_elim_round == DoubleElimRound.FINALS:
                return COMP_LEVELS_VERBOSE_FULL[CompLevel.F]
            else:
                return f"Double Elimination Bracket ({double_elim_round})"
        elif playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            if playoff_status["advanced_to_round_robin_finals"]:
                return COMP_LEVELS_VERBOSE_FULL[CompLevel.F]
            else:
                return (
                    f"Round Robin Bracket (Rank {playoff_status['round_robin_rank']})"
                )
        else:
            return COMP_LEVELS_VERBOSE_FULL[playoff_status["level"]]

    @classmethod
    def generate_playoff_status_string(
        cls,
        playoff: PlayoffAllianceStatus,
        pick: Optional[str],
        alliance_name: Optional[str],
        plural: bool = False,
        include_record: bool = True,
    ) -> List[str]:
        level = playoff["level"]
        status = playoff.get("status")
        record = playoff.get("record")
        playoff_average = playoff.get("playoff_average")
        playoff_type = playoff.get("playoff_type")

        level_str = cls.generate_playoff_level_status_string(playoff_type, playoff)

        if status == PlayoffOutcome.PLAYING:
            level_record = none_throws(playoff["current_level_record"])
            record_str = "{}-{}-{}".format(
                level_record["wins"],
                level_record["losses"],
                level_record["ties"],
            )
            if plural:
                playoff_str = "are <b>{}</b> in the <b>{}</b>".format(
                    record_str, level_str
                )
            else:
                playoff_str = "is <b>{}</b> in the <b>{}</b>".format(
                    record_str, level_str
                )

            if pick and alliance_name:
                playoff_str += " as the <b>{}</b> of <b>{}</b>".format(
                    pick, alliance_name
                )
            return [playoff_str]
        else:
            components = []
            if pick and alliance_name:
                components.append(
                    "competed in the playoffs as the <b>{}</b> of <b>{}</b>".format(
                        pick, alliance_name
                    )
                )

            if status == PlayoffOutcome.WON:
                if level == CompLevel.F:
                    playoff_str = "<b>won the event</b>"
                else:
                    playoff_str = "<b>won the {}</b>".format(level_str)
            elif status == PlayoffOutcome.ELIMINATED:
                if plural:
                    playoff_str = "were eliminated in the <b>{}</b>".format(level_str)
                else:
                    playoff_str = "was eliminated in the <b>{}</b>".format(level_str)
            else:
                raise Exception("Unknown playoff status: {}".format(status))
            if record and include_record:
                playoff_str += " with a playoff record of <b>{}-{}-{}</b>".format(
                    record["wins"], record["losses"], record["ties"]
                )
            if playoff_average and include_record:
                playoff_str += " with a playoff average of <b>{:.1f}</b>".format(
                    playoff_average
                )
            components.append(playoff_str)
            return components
