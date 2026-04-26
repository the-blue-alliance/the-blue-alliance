from typing import List

from backend.common.helpers.insights_v2.blue_banners import BlueBannersV2Calculator
from backend.common.helpers.insights_v2.compute import (
    compute_insights_for_year,
    InsightV2Calculator,
)
from backend.common.helpers.insights_v2.einstein_streak import (
    LongestEinsteinStreakV2Calculator,
)
from backend.common.helpers.insights_v2.most_matches_played import (
    MostMatchesPlayedV2Calculator,
)
from backend.common.helpers.insights_v2.most_matches_played_together import (
    MostMatchesPlayedTogetherV2Calculator,
)
from backend.common.helpers.insights_v2.qualifying_event_streak import (
    LongestQualifyingEventStreakV2Calculator,
)
from backend.common.models.insight_v2 import InsightV2
from backend.common.models.keys import Year


def make_all_insights(year: Year) -> List[InsightV2]:
    calculators: List[InsightV2Calculator] = [
        BlueBannersV2Calculator(),
        MostMatchesPlayedV2Calculator(),
        MostMatchesPlayedTogetherV2Calculator(),
    ]
    if year == 0:
        calculators += [
            LongestQualifyingEventStreakV2Calculator(),
            LongestEinsteinStreakV2Calculator(),
        ]
    return compute_insights_for_year(year, calculators)
