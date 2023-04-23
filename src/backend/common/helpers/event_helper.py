from collections import OrderedDict
from datetime import datetime, timedelta
from typing import cast, Dict, List, NamedTuple, Optional

from google.appengine.ext import ndb

from backend.common.consts import comp_level
from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.decorators import memoize
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match


CHAMPIONSHIP_EVENTS_LABEL = "FIRST Championship"
TWO_CHAMPS_LABEL = "FIRST Championship - {}"
FOC_LABEL = "FIRST Festival of Champions"
WEEKLESS_EVENTS_LABEL = "Other Official Events"
OFFSEASON_EVENTS_LABEL = "Offseason"
PRESEASON_EVENTS_LABEL = "Preseason"


class TeamAvgScore(NamedTuple):
    qual_avg: Optional[float]
    elim_avg: Optional[float]
    all_qual_scores: List[int]
    all_elim_scores: List[int]


class EventHelper(object):
    @classmethod
    def sorted_events(cls, events: List[Event]) -> List[Event]:
        """
        Sort events first by end date (ascending), and break ties by start date (ascending)
        Ex:
            e1 = Event(start_date=(2010, 3, 1), end_date=(2010, 3, 3))
            e2 = Event(start_date=(2010, 3, 2), end_date=(2010, 3, 4))
            e3 = Event(start_date=(2010, 3, 1), end_date=(2010, 3, 4))

            EventHelper.sorted_events([e1, e2, e3])
            > [e1, e3, e2]
        """
        return sorted(
            events,
            key=lambda x: (
                cls.end_date_or_distant_future(x),
                cls.start_date_or_distant_future(x),
            ),
        )

    @classmethod
    def start_date_or_distant_future(cls, event: Event) -> datetime:
        if not event.start_date:
            return datetime(2177, 1, 1, 1, 1, 1)
        else:
            return event.time_as_utc(event.start_date)

    @classmethod
    def end_date_or_distant_future(cls, event: Event) -> datetime:
        if not event.end_date:
            return datetime(2177, 1, 1, 1, 1, 1)
        else:
            return event.end_date

    @classmethod
    def group_by_week(cls, events: List[Event]) -> Dict[str, List[Event]]:
        """
        Events should already be ordered by start_date
        """
        to_return = OrderedDict()  # key: week_label, value: list of events

        weekless_events = []
        offseason_events = []
        preseason_events = []
        for event in events:
            if event.official and event.event_type_enum in {
                EventType.CMP_DIVISION,
                EventType.CMP_FINALS,
            }:
                if event.year >= 2017 and event.year <= 2020:
                    champs_label = TWO_CHAMPS_LABEL.format(event.city)
                else:
                    champs_label = CHAMPIONSHIP_EVENTS_LABEL
                if champs_label in to_return:
                    to_return[champs_label].append(event)
                else:
                    to_return[champs_label] = [event]
            elif event.official and event.event_type_enum in {
                EventType.REGIONAL,
                EventType.DISTRICT,
                EventType.DISTRICT_CMP_DIVISION,
                EventType.DISTRICT_CMP,
                EventType.REMOTE,
            }:
                if event.start_date is None or (
                    event.start_date.month == 12 and event.start_date.day == 31
                ):
                    weekless_events.append(event)
                else:
                    label = event.week_str
                    if label in to_return:
                        to_return[label].append(event)
                    else:
                        to_return[label] = [event]
            elif event.event_type_enum == EventType.FOC:
                if FOC_LABEL in to_return:
                    to_return[FOC_LABEL].append(event)
                else:
                    to_return[FOC_LABEL] = [event]
            elif event.event_type_enum == EventType.PRESEASON:
                preseason_events.append(event)
            else:
                # everything else is an offseason event
                offseason_events.append(event)

        # Add weekless + other events last
        if weekless_events:
            to_return[WEEKLESS_EVENTS_LABEL] = weekless_events
        if preseason_events:
            to_return[PRESEASON_EVENTS_LABEL] = preseason_events
        if offseason_events:
            to_return[OFFSEASON_EVENTS_LABEL] = offseason_events

        return to_return

    @staticmethod
    def is_2015_playoff(event_key: EventKey) -> bool:
        year = event_key[:4]
        event_short = event_key[4:]
        return year == "2015" and event_short not in {"cc", "cacc", "mttd"}

    @staticmethod
    def calculate_team_avg_score(
        team_key: TeamKey, matches: List[Match]
    ) -> TeamAvgScore:
        """
        Given a team_key and some matches, find the team's average qual and elim score
        """
        all_qual_scores: List[int] = []
        all_elim_scores: List[int] = []
        for match in matches:
            if match.has_been_played:
                for alliance in match.alliances.values():
                    if team_key in alliance["teams"]:
                        if match.comp_level in comp_level.ELIM_LEVELS:
                            all_elim_scores.append(alliance["score"])
                        else:
                            all_qual_scores.append(alliance["score"])
                        break
        qual_avg = (
            float(sum(all_qual_scores)) / len(all_qual_scores)
            if all_qual_scores != []
            else None
        )
        elim_avg = (
            float(sum(all_elim_scores)) / len(all_elim_scores)
            if all_elim_scores != []
            else None
        )
        return TeamAvgScore(
            qual_avg=qual_avg,
            elim_avg=elim_avg,
            all_qual_scores=all_qual_scores,
            all_elim_scores=all_elim_scores,
        )

    @staticmethod
    def calculate_wlt(team_key: TeamKey, matches: List[Match]) -> WLTRecord:
        """
        Given a team_key and some matches, find the Win Loss Tie.
        """
        wlt: WLTRecord = {"wins": 0, "losses": 0, "ties": 0}

        for match in matches:
            if match.has_been_played and match.winning_alliance is not None:
                if match.winning_alliance == "":
                    wlt["ties"] += 1
                elif (
                    team_key
                    in match.alliances[cast(AllianceColor, match.winning_alliance)][
                        "teams"
                    ]
                ):
                    wlt["wins"] += 1
                else:
                    wlt["losses"] += 1
        return wlt

    @classmethod
    @memoize(timeout=3600)  # 1 hour
    def events_within_a_day(cls) -> List[Event]:
        return list(filter(lambda e: e.within_a_day, cls.week_events()))

    @classmethod
    @memoize(timeout=3600)  # 1 hour
    def week_events(cls) -> List[Event]:
        """
        Get events this week
        In general, if an event is currently going on, it shows up in this query
        An event shows up in this query iff:
        a) The event is within_a_day
        OR
        b) The event.start_date is on or within 4 days after the closest Wednesday/Monday (pre-2020/post-2020)
        """
        today = datetime.today()

        # Make sure all events to be returned are within range
        two_weeks_of_events_keys_future = (
            Event.query()
            .filter(Event.start_date >= (today - timedelta(weeks=1)))
            .filter(Event.start_date <= (today + timedelta(weeks=1)))
            .order(Event.start_date)
            .fetch_async(keys_only=True)
        )

        events = []

        diff_from_week_start = 0 - today.weekday()
        closest_start_monday = today + timedelta(days=diff_from_week_start)

        two_weeks_of_event_futures = ndb.get_multi_async(
            two_weeks_of_events_keys_future.get_result()
        )
        for event_future in two_weeks_of_event_futures:
            event = event_future.get_result()
            if event.within_a_day:
                events.append(event)
            else:
                offset = event.start_date.date() - closest_start_monday.date()
                if (offset == timedelta(0)) or (
                    offset > timedelta(0) and offset < timedelta(weeks=1)
                ):
                    events.append(event)

        return cls.sorted_events(events)
