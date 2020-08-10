from typing import List, Optional, Set

from google.cloud import ndb
from pyre_extensions import none_throws, safe_cast
from typing_extensions import TypedDict

from backend.common.consts.ranking_sort_orders import (
    SORT_ORDER_INFO as RANKING_SORT_ORDERS,
)
from backend.common.models.alliance import EventAlliance
from backend.common.models.cached_model import CachedModel
from backend.common.models.event_district_points import EventDistrictPoints
from backend.common.models.event_insights import EventInsights
from backend.common.models.event_matchstats import EventMatchstats
from backend.common.models.event_predictions import EventPredictions
from backend.common.models.event_ranking import EventRanking
from backend.common.models.keys import EventKey
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class RenderedRankings(TypedDict):
    rankings: Optional[List[EventRanking]]
    sort_order_info: Optional[List[RankingSortOrderInfo]]
    extra_stats_info: List[RankingSortOrderInfo]


class EventDetails(CachedModel):
    """
    EventsDetails contains aggregate details about an event that tends to
    update often throughout an event. This includes rankings, event stats, etc.
    key_name is the event key, like '2010ct'
    """

    alliance_selections: List[
        EventAlliance
    ] = ndb.JsonProperty()  # Formatted as: [{'picks': [captain, pick1, pick2, 'frc123', ...], 'declines':[decline1, decline2, ...] }, {'picks': [], 'declines': []}, ... ]
    district_points: EventDistrictPoints = safe_cast(
        EventDistrictPoints, ndb.JsonProperty()
    )
    matchstats: EventMatchstats = safe_cast(
        EventMatchstats, ndb.JsonProperty()
    )  # for OPR, DPR, CCWM, etc.
    insights: EventInsights = safe_cast(EventInsights, ndb.JsonProperty())
    predictions: EventPredictions = safe_cast(EventPredictions, ndb.JsonProperty())
    rankings = ndb.JsonProperty()  # deprecated
    rankings2: List[EventRanking] = ndb.JsonProperty()

    # Based on the output of PlayoffAdvancementHelper.generatePlayoffAdvancement
    # Dict with keys for: bracket, playoff_advancement
    playoff_advancement = ndb.JsonProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    _mutable_attrs: Set[str] = {
        "alliance_selections",
        "district_points",
        "matchstats",
        "insights",
        "predictions",
        "rankings",
        "rankings2",
        "playoff_advancement",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "key": set(),
        }
        super(EventDetails, self).__init__(*args, **kw)

    @property
    def key_name(self) -> EventKey:
        return str(self.key.id())

    @property
    def year(self) -> int:
        return int(self.key_name[:4])

    @property
    def renderable_rankings(self) -> RenderedRankings:
        has_extra_stats = False
        if self.rankings2:
            for rank in self.rankings2:
                rank["extra_stats"] = []
                if self.year in {2017, 2018, 2019, 2020}:
                    rank["extra_stats"] = [
                        int(round(rank["sort_orders"][0] * rank["matches_played"])),
                    ]
                    has_extra_stats = True
                elif rank["qual_average"] is None:
                    rank["extra_stats"] = [
                        rank["sort_orders"][0] / rank["matches_played"]
                        if rank["matches_played"] > 0
                        else 0,
                    ]
                    has_extra_stats = True

        # 2015 mttd played the 2014 game
        ranking_year = 2014 if self.key_name == "2015mttd" else self.year
        sort_order_info = RANKING_SORT_ORDERS.get(ranking_year)

        extra_stats_info: List[RankingSortOrderInfo] = []
        if has_extra_stats:
            if self.year in {2017, 2018, 2019, 2020}:
                extra_stats_info = [{"name": "Total Ranking Points", "precision": 0}]
            elif sort_order_info is not None:
                extra_stats_info = [
                    {"name": f"{sort_order_info[0]['name']}/Match", "precision": 2}
                ]

        return {
            "rankings": self.rankings2,
            "sort_order_info": sort_order_info,
            "extra_stats_info": extra_stats_info,
        }

    @property
    def rankings_table(self) -> Optional[List[List[str]]]:
        if not self.rankings2:
            return None

        rankings = self.renderable_rankings
        # print(f"RANKINGS {rankings}")
        if rankings["sort_order_info"] is None:
            return None

        precisions = []
        for item in none_throws(rankings["sort_order_info"]):
            precisions.append(item["precision"])

        extra_precisions = []
        for item in rankings["extra_stats_info"]:
            extra_precisions.append(item["precision"])

        rankings_table = []
        has_record = False
        for rank in self.rankings2:
            row = [rank["rank"], rank["team_key"][3:]]
            # for i, item in enumerate(rank['sort_orders']):
            for i, precision in enumerate(precisions):
                # row.append('%.*f' % (precisions[i], round(item, precisions[i])))
                row.append(
                    "%.*f" % (precision, round(rank["sort_orders"][i], precision))
                )
            if rank["record"]:
                record = none_throws(rank["record"])
                row.append(f"{record['wins']}-{record['losses']}-{record['ties']}")
                has_record = True
            row.append(rank["dq"])
            row.append(rank["matches_played"])

            for i, precision in enumerate(extra_precisions):
                row.append(
                    "%.*f" % (precision, round(rank["extra_stats"][i], precision))
                )

            rankings_table.append(row)

        title_row = ["Rank", "Team"]
        for item in none_throws(rankings["sort_order_info"]):
            title_row.append(item["name"])
        if has_record:
            title_row += ["Record (W-L-T)"]
        title_row += ["DQ", "Played"]

        for item in rankings["extra_stats_info"]:
            title_row.append("{}*".format(item["name"]))

        rankings_table = [title_row] + rankings_table
        return rankings_table
