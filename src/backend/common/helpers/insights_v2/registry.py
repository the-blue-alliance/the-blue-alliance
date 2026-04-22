from typing import List

from backend.common.helpers.insights_v2.blue_banners import BlueBannersV2Calculator
from backend.common.helpers.insights_v2.compute import (
    compute_insights_for_year,
    InsightV2Calculator,
)
from backend.common.models.insight_v2 import InsightV2
from backend.common.models.keys import Year


def _build_calculators() -> List[InsightV2Calculator]:
    return [
        BlueBannersV2Calculator(),
    ]


def make_all_insights(year: Year) -> List[InsightV2]:
    return compute_insights_for_year(year, _build_calculators())
