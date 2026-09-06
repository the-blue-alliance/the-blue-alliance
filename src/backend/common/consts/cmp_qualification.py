import enum
from typing import Dict, FrozenSet, NamedTuple, Set, Tuple

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.string_enum import StrEnum
from backend.common.models.keys import TeamKey, Year

HALL_OF_FAME_MANUAL_LIST_FIRST_YEAR: Year = 2022

HALL_OF_FAME_TEAMS_BY_YEAR: Dict[Year, Set[TeamKey]] = {
    2022: {
        "frc27",
        "frc503",
        "frc597",
        "frc987",
        "frc1114",
        "frc1311",
        "frc1538",
        "frc1816",
        "frc1902",
        "frc2614",
        "frc2834",
        "frc3132",
        "frc4613",
    },
    2023: {
        "frc27",
        "frc359",
        "frc503",
        "frc597",
        "frc987",
        "frc1114",
        "frc1311",
        "frc1538",
        "frc1629",
        "frc1816",
        "frc1902",
        "frc2614",
        "frc2834",
        "frc3132",
        "frc4613",
    },
    2024: {
        "frc27",
        "frc321",
        "frc359",
        "frc503",
        "frc597",
        "frc987",
        "frc1114",
        "frc1538",
        "frc1629",
        "frc1816",
        "frc1902",
        "frc2614",
        "frc2834",
        "frc3132",
        "frc4613",
    },
    2025: {
        "frc27",
        "frc321",
        "frc503",
        "frc597",
        "frc987",
        "frc1114",
        "frc1538",
        "frc1629",
        "frc1816",
        "frc1902",
        "frc2486",
        "frc2614",
        "frc2834",
        "frc3132",
        "frc4613",
    },
    2026: {
        "frc5985",
        "frc2486",
        "frc321",
        "frc1629",
        "frc503",
        "frc4613",
        "frc1816",
        "frc1902",
        "frc1311",
        "frc2834",
    },
}

ORIGINAL_AND_SUSTAINING_TEAMS: Set[TeamKey] = {
    "frc20",
    "frc45",
    "frc126",
    "frc148",
    "frc151",
    "frc157",
    "frc190",
    "frc191",
    "frc250",
}


@enum.unique
class CmpQualificationMethod(StrEnum):
    DISTRICT_POINTS = "district_points"
    WAITLIST = "waitlist"
    ORIGINAL_AND_SUSTAINING = "original_and_sustaining"
    HALL_OF_FAME = "hall_of_fame"
    PRIOR_YEAR_CMP_WINNER = "prior_year_cmp_winner"
    PRIOR_YEAR_CMP_IMPACT = "prior_year_cmp_impact"
    PRIOR_YEAR_CMP_ENGINEERING_INSPIRATION = "prior_year_cmp_engineering_inspiration"
    REGIONAL_WINNER = "regional_winner"
    REGIONAL_IMPACT = "regional_impact"
    REGIONAL_ENGINEERING_INSPIRATION = "regional_engineering_inspiration"
    REGIONAL_WILDCARD = "regional_wildcard"
    LATE_REGIONAL_WINNER = "late_regional_winner"
    LATE_REGIONAL_IMPACT = "late_regional_impact"
    LATE_REGIONAL_ENGINEERING_INSPIRATION = "late_regional_engineering_inspiration"
    LATE_REGIONAL_WILDCARD = "late_regional_wildcard"
    DCMP_WINNER = "dcmp_winner"
    DCMP_IMPACT = "dcmp_impact"
    DCMP_ENGINEERING_INSPIRATION = "dcmp_engineering_inspiration"
    DCMP_ROOKIE_ALL_STAR = "dcmp_rookie_all_star"


class CmpQualificationRule(NamedTuple):
    year_start: Year
    year_end: Year
    eats_district_slot: bool

    def applies_to(self, year: Year) -> bool:
        return self.year_start <= year <= self.year_end


CMP_QUALIFICATION_RULES: Dict[CmpQualificationMethod, CmpQualificationRule] = {
    CmpQualificationMethod.DISTRICT_POINTS: CmpQualificationRule(
        year_start=2009,
        year_end=9999,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.WAITLIST: CmpQualificationRule(
        year_start=1992,
        year_end=9999,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.ORIGINAL_AND_SUSTAINING: CmpQualificationRule(
        year_start=1992,
        year_end=2019,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.HALL_OF_FAME: CmpQualificationRule(
        year_start=1992,
        year_end=9999,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.PRIOR_YEAR_CMP_WINNER: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.PRIOR_YEAR_CMP_IMPACT: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.PRIOR_YEAR_CMP_ENGINEERING_INSPIRATION: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.REGIONAL_WINNER: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.REGIONAL_IMPACT: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.REGIONAL_ENGINEERING_INSPIRATION: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.REGIONAL_WILDCARD: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.LATE_REGIONAL_WINNER: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.LATE_REGIONAL_IMPACT: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.LATE_REGIONAL_ENGINEERING_INSPIRATION: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.LATE_REGIONAL_WILDCARD: CmpQualificationRule(
        year_start=1992,
        year_end=2025,
        eats_district_slot=False,
    ),
    CmpQualificationMethod.DCMP_WINNER: CmpQualificationRule(
        year_start=2009,
        year_end=9999,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.DCMP_IMPACT: CmpQualificationRule(
        year_start=2009,
        year_end=9999,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.DCMP_ENGINEERING_INSPIRATION: CmpQualificationRule(
        year_start=2009,
        year_end=9999,
        eats_district_slot=True,
    ),
    CmpQualificationMethod.DCMP_ROOKIE_ALL_STAR: CmpQualificationRule(
        year_start=2009,
        year_end=9999,
        eats_district_slot=True,
    ),
}


DCMP_FINALS_ONLY: FrozenSet[EventType] = frozenset({EventType.DISTRICT_CMP})
DCMP_ANY_FIELD: FrozenSet[EventType] = frozenset(
    {EventType.DISTRICT_CMP, EventType.DISTRICT_CMP_DIVISION}
)

DCMP_AWARD_METHODS: Dict[
    CmpQualificationMethod, Tuple[FrozenSet[EventType], AwardType]
] = {
    CmpQualificationMethod.DCMP_WINNER: (DCMP_FINALS_ONLY, AwardType.WINNER),
    CmpQualificationMethod.DCMP_IMPACT: (DCMP_ANY_FIELD, AwardType.CHAIRMANS),
    CmpQualificationMethod.DCMP_ENGINEERING_INSPIRATION: (
        DCMP_ANY_FIELD,
        AwardType.ENGINEERING_INSPIRATION,
    ),
    CmpQualificationMethod.DCMP_ROOKIE_ALL_STAR: (
        DCMP_ANY_FIELD,
        AwardType.ROOKIE_ALL_STAR,
    ),
}

REGIONAL_AWARD_METHODS: Dict[CmpQualificationMethod, AwardType] = {
    CmpQualificationMethod.REGIONAL_WINNER: AwardType.WINNER,
    CmpQualificationMethod.REGIONAL_IMPACT: AwardType.CHAIRMANS,
    CmpQualificationMethod.REGIONAL_ENGINEERING_INSPIRATION: AwardType.ENGINEERING_INSPIRATION,
    CmpQualificationMethod.REGIONAL_WILDCARD: AwardType.WILDCARD,
}

LATE_REGIONAL_AWARD_METHODS: Dict[CmpQualificationMethod, AwardType] = {
    CmpQualificationMethod.LATE_REGIONAL_WINNER: AwardType.WINNER,
    CmpQualificationMethod.LATE_REGIONAL_IMPACT: AwardType.CHAIRMANS,
    CmpQualificationMethod.LATE_REGIONAL_ENGINEERING_INSPIRATION: AwardType.ENGINEERING_INSPIRATION,
    CmpQualificationMethod.LATE_REGIONAL_WILDCARD: AwardType.WILDCARD,
}

PRIOR_YEAR_CMP_AWARD_METHODS: Dict[
    CmpQualificationMethod, Tuple[EventType, AwardType]
] = {
    CmpQualificationMethod.PRIOR_YEAR_CMP_WINNER: (
        EventType.CMP_FINALS,
        AwardType.WINNER,
    ),
    CmpQualificationMethod.PRIOR_YEAR_CMP_IMPACT: (
        EventType.CMP_FINALS,
        AwardType.CHAIRMANS,
    ),
    CmpQualificationMethod.PRIOR_YEAR_CMP_ENGINEERING_INSPIRATION: (
        EventType.CMP_DIVISION,
        AwardType.ENGINEERING_INSPIRATION,
    ),
}
