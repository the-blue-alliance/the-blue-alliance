from __future__ import annotations
import enum
from typing import Dict, Set


@enum.unique
class EventType(enum.IntEnum):
    REGIONAL = 0
    DISTRICT = 1
    DISTRICT_CMP = 2
    CMP_DIVISION = 3
    CMP_FINALS = 4
    DISTRICT_CMP_DIVISION = 5
    FOC = 6

    OFFSEASON = 99
    PRESEASON = 100
    UNLABLED = -1


TYPE_NAMES: Dict[EventType, str] = {
    EventType.REGIONAL: "Regional",
    EventType.DISTRICT: "District",
    EventType.DISTRICT_CMP_DIVISION: "District Championship Division",
    EventType.DISTRICT_CMP: "District Championship",
    EventType.CMP_DIVISION: "Championship Division",
    EventType.CMP_FINALS: "Championship Finals",
    EventType.FOC: "Festival of Champions",
    EventType.OFFSEASON: "Offseason",
    EventType.PRESEASON: "Preseason",
    EventType.UNLABLED: "--",
}


SHORT_TYPE_NAMES: Dict[EventType, str] = {
    EventType.REGIONAL: "Regional",
    EventType.DISTRICT: "District",
    EventType.DISTRICT_CMP_DIVISION: "District Championship Division",
    EventType.DISTRICT_CMP: "District Championship",
    EventType.CMP_DIVISION: "Division",
    EventType.CMP_FINALS: "Championship",
    EventType.FOC: "FoC",
    EventType.OFFSEASON: "Offseason",
    EventType.PRESEASON: "Preseason",
    EventType.UNLABLED: "--",
}


DISTRICT_EVENT_TYPES: Set[EventType] = {
    EventType.DISTRICT,
    EventType.DISTRICT_CMP_DIVISION,
    EventType.DISTRICT_CMP,
}


NON_CMP_EVENT_TYPES: Set[EventType] = {
    EventType.REGIONAL,
    EventType.DISTRICT,
    EventType.DISTRICT_CMP_DIVISION,
    EventType.DISTRICT_CMP,
}

CMP_EVENT_TYPES: Set[EventType] = {
    EventType.CMP_DIVISION,
    EventType.CMP_FINALS,
}


SEASON_EVENT_TYPES: Set[EventType] = {
    EventType.REGIONAL,
    EventType.DISTRICT,
    EventType.DISTRICT_CMP_DIVISION,
    EventType.DISTRICT_CMP,
    EventType.CMP_DIVISION,
    EventType.CMP_FINALS,
    EventType.FOC,
}
