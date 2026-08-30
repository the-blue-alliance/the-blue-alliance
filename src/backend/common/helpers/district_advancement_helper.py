import heapq
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTiebreakers,
)
from backend.common.models.district import District
from backend.common.models.district_advancement import DistrictAdvancementCutoffs
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.keys import EventKey, TeamKey
from backend.common.queries.award_query import EventAwardsQuery


class DcmpCutoffs(NamedTuple):
    original: int
    effective: int
    declined: List[TeamKey]


class DistrictAdvancementHelper:
    @classmethod
    def _competed_at_dcmp(cls, ranking: DistrictRanking) -> bool:
        return any(
            event_points.get("district_cmp")
            and (
                event_points["qual_points"]
                or event_points["elim_points"]
                or event_points["alliance_points"]
            )
            for event_points in ranking["event_points"]
        )

    @classmethod
    def dcmp_attendance(cls, rankings: Sequence[DistrictRanking]) -> Set[TeamKey]:
        return {r["team_key"] for r in rankings if cls._competed_at_dcmp(r)}

    @classmethod
    def match_scores_by_event(
        cls, events: Sequence[Event]
    ) -> Dict[EventKey, Dict[TeamKey, List[int]]]:
        return {
            event.key_name: {
                team_key: tiebreakers.get("highest_match_scores", [])
                for team_key, tiebreakers in event.district_points.get(
                    "tiebreakers", {}
                ).items()
            }
            for event in events
            if event.district_points
        }

    @classmethod
    def pre_dcmp_rankings(
        cls,
        rankings: Sequence[DistrictRanking],
        match_scores: Optional[Dict[EventKey, Dict[TeamKey, List[int]]]] = None,
    ) -> List[DistrictRanking]:
        match_scores = match_scores or {}
        adjusted: List[Tuple[Tuple[int, ...], DistrictRanking]] = []
        for ranking in rankings:
            kept: List[TeamAtEventDistrictPoints] = [
                ep for ep in ranking["event_points"] if not ep.get("district_cmp")
            ]
            dcmp_total = sum(
                ep["total"] for ep in ranking["event_points"] if ep.get("district_cmp")
            )
            elim = [ep["elim_points"] for ep in kept]
            alliance = [ep["alliance_points"] for ep in kept]

            pre_dcmp = DistrictRanking(
                rank=ranking["rank"],
                team_key=ranking["team_key"],
                point_total=ranking["point_total"] - dcmp_total,
                rookie_bonus=ranking["rookie_bonus"],
                event_points=kept,
            )
            if "other_bonus" in ranking:
                pre_dcmp["other_bonus"] = ranking["other_bonus"]
            if "adjustments" in ranking:
                pre_dcmp["adjustments"] = ranking["adjustments"]

            top_match_scores = heapq.nlargest(
                3,
                [
                    score
                    for ep in kept
                    for score in match_scores.get(ep["event_key"], {}).get(
                        ranking["team_key"], []
                    )
                ],
            )
            top_match_scores += [0] * (3 - len(top_match_scores))

            tiebreakers = DistrictRankingTiebreakers(
                total_playoff_points=sum(elim),
                best_playoff_points=max(elim, default=0),
                total_alliance_points=sum(alliance),
                best_alliance_points=max(alliance, default=0),
                total_qual_points=sum(ep["qual_points"] for ep in kept),
            )
            sort_key = tuple(
                DistrictHelper.ranking_sort_key(
                    pre_dcmp["point_total"], tiebreakers, top_match_scores
                )
            ) + (ranking["rank"],)
            adjusted.append((sort_key, pre_dcmp))

        adjusted.sort(key=lambda item: item[0])

        ordered = [ranking for _, ranking in adjusted]
        for rank, ranking in enumerate(ordered, start=1):
            ranking["rank"] = rank
        return ordered

    @classmethod
    def calculate_dcmp_cutoffs(
        cls,
        pre_dcmp_rankings: Sequence[DistrictRanking],
        slots: int,
        auto_qualified: Set[TeamKey],
        attendance: Set[TeamKey],
    ) -> DcmpCutoffs:
        ranked_teams = {r["team_key"] for r in pre_dcmp_rankings}
        invited = auto_qualified & ranked_teams

        remaining = slots - len(invited)
        original = 0
        for ranking in pre_dcmp_rankings:
            if remaining <= 0:
                break
            if ranking["team_key"] in invited:
                continue
            original = ranking["point_total"]
            remaining -= 1

        points_attendees = [
            r
            for r in pre_dcmp_rankings
            if r["team_key"] in attendance and r["team_key"] not in auto_qualified
        ]
        if not points_attendees:
            return DcmpCutoffs(original=original, effective=0, declined=[])

        lowest = points_attendees[-1]
        declined = [
            r["team_key"]
            for r in pre_dcmp_rankings
            if r["rank"] < lowest["rank"]
            and r["team_key"] not in auto_qualified
            and r["team_key"] not in attendance
        ]
        return DcmpCutoffs(
            original=original,
            effective=lowest["point_total"],
            declined=declined,
        )

    @classmethod
    def impact_award_winners(cls, events: Sequence[Event]) -> Set[TeamKey]:
        winners: Set[TeamKey] = set()
        award_futures = [
            EventAwardsQuery(event_key=event.key_name).fetch_async()
            for event in events
            if event.event_type_enum == EventType.DISTRICT
        ]
        for future in award_futures:
            for award in future.get_result():
                if award.award_type_enum != AwardType.CHAIRMANS:
                    continue
                winners.update(team.id() for team in award.team_list)
        return winners

    @classmethod
    def calculate_for_district(
        cls, district: District, events: Sequence[Event]
    ) -> Optional[DistrictAdvancementCutoffs]:
        rankings = district.rankings
        if not rankings:
            return None

        attendance = cls.dcmp_attendance(rankings)
        if not attendance:
            return None

        dcmp = cls.calculate_dcmp_cutoffs(
            cls.pre_dcmp_rankings(rankings, cls.match_scores_by_event(events)),
            district.official_advancement_counts["dcmp"],
            cls.impact_award_winners(events),
            attendance,
        )
        return DistrictAdvancementCutoffs(
            dcmp_original=dcmp.original,
            dcmp_effective=dcmp.effective,
            dcmp_declines=dcmp.declined,
            cmp_original=0,
            cmp_effective=0,
            cmp_declines=[],
        )
