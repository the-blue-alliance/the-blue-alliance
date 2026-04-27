import logging
import re
from typing import Dict, Optional

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.consts.playoff_type import (
    DOUBLE_ELIM_4_MAPPING,
    DOUBLE_ELIM_MAPPING,
    LEGACY_DOUBLE_ELIM_MAPPING,
    PlayoffType,
)
from backend.common.datafeeds.parsers.parser_base import ParserBase
from backend.common.helpers.playoff_type_helper import PlayoffTypeHelper
from backend.common.models.event import Event
from backend.common.models.event_queue_status import (
    EventQueueStatus,
    NexusCurrentlyQueueing,
    NexusMatch,
    NexusMatchTiming,
)
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.common.nexus_api.types import EventStatus

# Nexus labels finals "Final 1/2/3" but TBA continues its match numbering
# from the semifinal bracket. Offset = (first F key in the mapping) - 1.
_FINALS_LABEL_OFFSET: dict[PlayoffType, int] = {
    playoff_type: min(k for k, (level, _, _) in mapping.items() if level == CompLevel.F)
    - 1
    for playoff_type, mapping in (
        (PlayoffType.DOUBLE_ELIM_8_TEAM, DOUBLE_ELIM_MAPPING),
        (PlayoffType.DOUBLE_ELIM_4_TEAM, DOUBLE_ELIM_4_MAPPING),
        (PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM, LEGACY_DOUBLE_ELIM_MAPPING),
    )
}


class NexusAPIQueueStatusParser(ParserBase[EventStatus, Optional[EventQueueStatus]]):

    MATCH_LABEL_PATTERN: re.Pattern = re.compile(
        r"(Practice|Qualification|Playoff|Final) (\d+)( Replay)?"
    )

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event
        self.matches = event.matches

    def parse(self, response: EventStatus) -> Optional[EventQueueStatus]:
        if not isinstance(response, dict):
            return None

        nexus_matches = response.get("matches")
        if not isinstance(nexus_matches, list):
            return None

        now_queueing_match_key: Optional[MatchKey] = None
        matches: Dict[MatchKey, NexusMatch] = {}
        for api_match in nexus_matches:
            match_key = self._parse_match_description(api_match["label"])
            if not match_key:
                continue

            match = next((m for m in self.matches if match_key == m.key_name), None)
            if not match:
                continue

            matches[match_key] = NexusMatch(
                label=api_match["label"],
                status=NexusMatchStatus.from_string(api_match["status"]),
                played=match.has_been_played,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=api_match["times"].get(
                        "estimatedQueueTime"
                    ),
                    estimated_start_time_ms=api_match["times"].get(
                        "estimatedStartTime"
                    ),
                ),
            )
            if response.get("nowQueuing") == api_match["label"]:
                now_queueing_match_key = match_key

        return EventQueueStatus(
            data_as_of_ms=int(response["dataAsOfTime"]),
            now_queueing=(
                NexusCurrentlyQueueing(
                    match_key=now_queueing_match_key,
                    match_name=str(response["nowQueuing"]),
                )
                if now_queueing_match_key
                else None
            ),
            matches=matches,
        )

    def _parse_match_description(self, description: str) -> Optional[MatchKey]:
        re_match = self.MATCH_LABEL_PATTERN.match(description)
        if not re_match:
            logging.warning(f"Unable to parse nexus match label: {description}")
            return None

        level = re_match.group(1)
        level_number = int(re_match.group(2))
        if level == "Practice":
            # Practice matches aren't currently supported
            return None

        if level == "Final":
            # Nexus reports "Final 1, 2, 3" while TBA's match numbering
            # continues from the semifinal bracket — the offset depends on
            # the playoff format.
            level_number += _FINALS_LABEL_OFFSET.get(self.event.playoff_type, 0)

        try:
            comp_level = PlayoffTypeHelper.get_comp_level(
                self.event.playoff_type, level, level_number
            )
            set_number, match_number = PlayoffTypeHelper.get_set_match_number(
                self.event.playoff_type, comp_level, level_number
            )
        except KeyError:
            logging.warning(
                f"Unable to map nexus match label {description!r} for {self.event.key_name} (playoff_type={self.event.playoff_type})"
            )
            return None
        return Match.render_key_name(
            self.event.key_name, comp_level.value, set_number, match_number
        )
