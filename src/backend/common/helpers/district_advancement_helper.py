import heapq
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Set, Tuple

from pyre_extensions import none_throws

from backend.common.consts.award_type import AwardType
from backend.common.consts.cmp_qualification import (
    CMP_QUALIFICATION_RULES,
    CmpQualificationMethod,
    DCMP_AWARD_METHODS,
    HALL_OF_FAME_MANUAL_LIST_FIRST_YEAR,
    HALL_OF_FAME_TEAMS_BY_YEAR,
    LATE_REGIONAL_AWARD_METHODS,
    ORIGINAL_AND_SUSTAINING_TEAMS,
    PRIOR_YEAR_CMP_AWARD_METHODS,
    REGIONAL_AWARD_METHODS,
)
from backend.common.consts.event_type import EventType
from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTiebreakers,
)
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_advancement import DistrictAdvancementCutoffs
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.queries.award_query import (
    EventAwardsQuery,
    EventTypeAwardsQuery,
    YearEventTypeAwardsQuery,
)
from backend.common.queries.event_query import CmpDivisionsInYearQuery

NO_POINTS_CUTOFF: int = -1

DCMP_EVENT_TYPES: Set[EventType] = {
    EventType.DISTRICT_CMP,
    EventType.DISTRICT_CMP_DIVISION,
}


class Cutoffs(NamedTuple):
    original: int
    effective: int
    declined: List[TeamKey]
    waitlisted: List[TeamKey]
    points_invited: List[TeamKey]


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
    def calculate_cutoffs(
        cls,
        rankings: Sequence[DistrictRanking],
        slots: int,
        consuming: Set[TeamKey],
        non_consuming: Set[TeamKey],
        attendance: Set[TeamKey],
        cap_to_slots: bool,
    ) -> Cutoffs:
        ranked_teams = {r["team_key"] for r in rankings}
        invited = consuming & ranked_teams
        points_slots = max(slots - len(invited), 0)
        pool = [
            r
            for r in rankings
            if r["team_key"] not in consuming and r["team_key"] not in non_consuming
        ]

        original = (
            pool[min(points_slots, len(pool)) - 1]["point_total"]
            if points_slots and pool
            else NO_POINTS_CUTOFF
        )

        pool_attendees = [r for r in pool if r["team_key"] in attendance]
        cap = (
            max(slots - len(invited & attendance), 0)
            if cap_to_slots
            else len(pool_attendees)
        )
        attendees = pool_attendees[:cap]
        waitlisted = [r["team_key"] for r in pool_attendees[cap:]]
        if not attendees:
            return Cutoffs(
                original=original,
                effective=0,
                declined=[],
                waitlisted=waitlisted,
                points_invited=[],
            )

        lowest = attendees[-1]
        declined = [
            r["team_key"]
            for r in rankings
            if r["rank"] < lowest["rank"]
            and r["team_key"] not in non_consuming
            and r["team_key"] not in attendance
        ]
        return Cutoffs(
            original=original,
            effective=lowest["point_total"],
            declined=declined,
            waitlisted=waitlisted,
            points_invited=[r["team_key"] for r in pool if r["rank"] <= lowest["rank"]],
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
    def _award_team_keys(cls, awards: Sequence[Award]) -> Set[TeamKey]:
        return {
            none_throws(team.string_id())
            for award in awards
            for team in award.team_list
        }

    @classmethod
    def cmp_attendance(cls, year: Year) -> Set[TeamKey]:
        attendance: Set[TeamKey] = set()
        for event in CmpDivisionsInYearQuery(year=year).fetch():
            for key in EventTeam.query(EventTeam.event == event.key).fetch(
                keys_only=True
            ):
                attendance.add(none_throws(key.string_id()).split("_")[1])
        return attendance

    @classmethod
    def hall_of_fame_teams(cls, year: Year) -> Set[TeamKey]:
        return cls._award_team_keys(
            [
                award
                for award in EventTypeAwardsQuery(
                    event_type=EventType.CMP_FINALS, award_type=AwardType.CHAIRMANS
                ).fetch()
                if award.year < year
            ]
        )

    @classmethod
    def prior_year_cmp_teams(
        cls, year: Year, event_type: EventType, award_type: AwardType
    ) -> Set[TeamKey]:
        return cls._award_team_keys(
            YearEventTypeAwardsQuery(
                year=year - 1,
                event_type=event_type,
                award_type=award_type,
            ).fetch()
        )

    @classmethod
    def regional_award_qualifiers(
        cls, year: Year, award_type: AwardType
    ) -> Dict[TeamKey, List[int]]:
        event_weeks: Dict[EventKey, Optional[int]] = {}
        qualifiers: Dict[TeamKey, List[int]] = {}
        for award in YearEventTypeAwardsQuery(
            year=year, event_type=EventType.REGIONAL, award_type=award_type
        ).fetch():
            event_key = none_throws(award.event.string_id())
            if event_key not in event_weeks:
                event = award.event.get()
                event_weeks[event_key] = event.week if event else None
            week = event_weeks[event_key]
            for team in award.team_list:
                weeks = qualifiers.setdefault(none_throws(team.string_id()), [])
                if week is not None:
                    weeks.append(week)
        return qualifiers

    @classmethod
    def dcmp_awards(cls, events: Sequence[Event]) -> List[Award]:
        award_futures = [
            EventAwardsQuery(event_key=event.key_name).fetch_async()
            for event in events
            if event.event_type_enum in DCMP_EVENT_TYPES
        ]
        return [award for future in award_futures for award in future.get_result()]

    @classmethod
    def award_winners(
        cls,
        awards: Sequence[Award],
        event_types: FrozenSet[EventType],
        award_type: AwardType,
    ) -> Set[TeamKey]:
        return cls._award_team_keys(
            [
                award
                for award in awards
                if award.award_type_enum == award_type
                and award.event_type_enum in event_types
            ]
        )

    @classmethod
    def dcmp_week(cls, events: Sequence[Event]) -> Optional[int]:
        weeks = [
            event.week
            for event in events
            if event.event_type_enum in DCMP_EVENT_TYPES and event.week is not None
        ]
        return min(weeks) if weeks else None

    @classmethod
    def cmp_allows_unqualified_attendees(cls, year: Year) -> bool:
        return cls._applies(CmpQualificationMethod.WAITLIST, year)

    @classmethod
    def _applies(cls, method: CmpQualificationMethod, year: Year) -> bool:
        return CMP_QUALIFICATION_RULES[method].applies_to(year)

    @classmethod
    def cmp_qualifiers_by_method(
        cls, district: District, events: Sequence[Event]
    ) -> Dict[CmpQualificationMethod, Set[TeamKey]]:
        year = district.year
        derived: Dict[CmpQualificationMethod, Set[TeamKey]] = {}

        if cls._applies(CmpQualificationMethod.ORIGINAL_AND_SUSTAINING, year):
            derived[CmpQualificationMethod.ORIGINAL_AND_SUSTAINING] = set(
                ORIGINAL_AND_SUSTAINING_TEAMS
            )
        if cls._applies(CmpQualificationMethod.HALL_OF_FAME, year):
            derived[CmpQualificationMethod.HALL_OF_FAME] = (
                set(HALL_OF_FAME_TEAMS_BY_YEAR.get(year, set()))
                if year >= HALL_OF_FAME_MANUAL_LIST_FIRST_YEAR
                else cls.hall_of_fame_teams(year)
            )

        for method, (event_type, award_type) in PRIOR_YEAR_CMP_AWARD_METHODS.items():
            if cls._applies(method, year):
                derived[method] = cls.prior_year_cmp_teams(year, event_type, award_type)

        active_dcmp_methods = {
            method: source
            for method, source in DCMP_AWARD_METHODS.items()
            if cls._applies(method, year)
        }
        if active_dcmp_methods:
            dcmp_awards = cls.dcmp_awards(events)
            for method, (event_types, award_type) in active_dcmp_methods.items():
                derived[method] = cls.award_winners(
                    dcmp_awards, event_types, award_type
                )

        dcmp_week = cls.dcmp_week(events)
        for methods, wanted_before_dcmp in (
            (REGIONAL_AWARD_METHODS, True),
            (LATE_REGIONAL_AWARD_METHODS, False),
        ):
            for method, award_type in methods.items():
                if not cls._applies(method, year):
                    continue
                derived[method] = {
                    team_key
                    for team_key, weeks in cls.regional_award_qualifiers(
                        year, award_type
                    ).items()
                    if (
                        dcmp_week is not None
                        and any(week < dcmp_week for week in weeks)
                    )
                    == wanted_before_dcmp
                }

        return derived

    @classmethod
    def cmp_qualifiers(
        cls, district: District, events: Sequence[Event]
    ) -> Tuple[Set[TeamKey], Set[TeamKey]]:
        consuming: Set[TeamKey] = set()
        non_consuming: Set[TeamKey] = set()

        for method, teams in cls.cmp_qualifiers_by_method(district, events).items():
            if CMP_QUALIFICATION_RULES[method].eats_district_slot:
                consuming |= teams
            else:
                non_consuming |= teams

        return consuming, non_consuming - consuming

    @classmethod
    def cmp_cutoffs(
        cls, district: District, events: Sequence[Event]
    ) -> Optional[Cutoffs]:
        rankings = district.rankings
        attendance = cls.cmp_attendance(district.year) & {
            r["team_key"] for r in rankings
        }
        if not attendance:
            return None

        consuming, non_consuming = cls.cmp_qualifiers(district, events)
        return cls.calculate_cutoffs(
            rankings,
            district.official_advancement_counts["cmp"],
            consuming,
            non_consuming,
            attendance,
            cap_to_slots=cls.cmp_allows_unqualified_attendees(district.year),
        )

    @classmethod
    def cmp_qualification_methods(
        cls, district: District, events: Sequence[Event]
    ) -> Dict[TeamKey, CmpQualificationMethod]:
        ranked = {r["team_key"] for r in district.rankings}
        by_method = cls.cmp_qualifiers_by_method(district, events)
        methods: Dict[TeamKey, CmpQualificationMethod] = {}

        for eats_district_slot in (True, False):
            for method in CmpQualificationMethod:
                if CMP_QUALIFICATION_RULES[method].eats_district_slot != (
                    eats_district_slot
                ):
                    continue
                for team_key in sorted(by_method.get(method, set()) & ranked):
                    methods.setdefault(team_key, method)

        cutoffs = cls.cmp_cutoffs(district, events)
        if cutoffs is None:
            return methods

        for team_key in cutoffs.points_invited:
            methods.setdefault(team_key, CmpQualificationMethod.DISTRICT_POINTS)
        for team_key in cutoffs.waitlisted:
            methods.setdefault(team_key, CmpQualificationMethod.WAITLIST)
        return methods

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

        slots = district.official_advancement_counts
        dcmp = cls.calculate_cutoffs(
            cls.pre_dcmp_rankings(rankings, cls.match_scores_by_event(events)),
            slots["dcmp"],
            cls.impact_award_winners(events),
            set(),
            attendance,
            cap_to_slots=False,
        )

        cmp = cls.cmp_cutoffs(district, events)
        qualification = cls.cmp_qualification_methods(district, events)
        if cmp is None:
            previous = district.advancement_cutoffs
            cmp = Cutoffs(
                original=previous["cmp_original"] if previous else 0,
                effective=previous["cmp_effective"] if previous else 0,
                declined=previous["cmp_declines"] if previous else [],
                waitlisted=[],
                points_invited=[],
            )
            qualification = (
                previous["cmp_qualification"]
                if previous and "cmp_qualification" in previous
                else {}
            )

        return DistrictAdvancementCutoffs(
            dcmp_original=dcmp.original,
            dcmp_effective=dcmp.effective,
            dcmp_declines=dcmp.declined,
            cmp_original=cmp.original,
            cmp_effective=cmp.effective,
            cmp_declines=cmp.declined,
            cmp_qualification=qualification,
        )
