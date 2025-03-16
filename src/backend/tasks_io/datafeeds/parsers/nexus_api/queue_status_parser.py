import logging
import re
from typing import Dict, Optional

from pyre_extensions import JSON

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.consts.playoff_type import PlayoffType
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
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class NexusAPIQueueStatusParser(ParserBase[Optional[EventQueueStatus]]):

    MATCH_LABEL_PATTERN: re.Pattern = re.compile(
        r"(Practice|Qualification|Playoff|Final) (\d+)( Replay)?"
    )

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event
        self.matches = event.matches

    def parse(self, response: JSON) -> Optional[EventQueueStatus]:
        if self.event.playoff_type != PlayoffType.DOUBLE_ELIM_8_TEAM:
            logging.warning(
                f"Unable to parse nexus status for {self.event.key_name}, playoff type is {self.event.playoff_type}"
            )

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
                    estimated_queue_time_ms=api_match["times"]["estimatedQueueTime"],
                    estimated_start_time_ms=api_match["times"]["estimatedStartTime"],
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
            # Nexus will report "Final 1, 2, 3"
            # While FMS match nubmering does not reset for finals
            # This assumes a double elim format
            level_number += 13

        comp_level = PlayoffTypeHelper.get_comp_level(
            self.event.playoff_type, level, level_number
        )

        set_number, match_number = PlayoffTypeHelper.get_set_match_number(
            self.event.playoff_type, comp_level, level_number
        )
        return Match.render_key_name(
            self.event.key_name, comp_level.value, set_number, match_number
        )
