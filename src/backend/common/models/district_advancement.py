from typing import Dict, List, TypedDict

from backend.common.consts.cmp_qualification import CmpQualificationMethod
from backend.common.models.keys import TeamKey


class TeamDistrictAdvancement(TypedDict):
    dcmp: bool
    cmp: bool


DistrictAdvancement = Dict[TeamKey, TeamDistrictAdvancement]


class AdvancementCounts(TypedDict):
    dcmp: int
    cmp: int


class DistrictAdvancementCutoffs(TypedDict):
    dcmp_original: int
    dcmp_effective: int
    dcmp_declines: List[TeamKey]
    cmp_original: int
    cmp_effective: int
    cmp_declines: List[TeamKey]
    cmp_qualification: Dict[TeamKey, CmpQualificationMethod]
