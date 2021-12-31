from typing import List, Tuple

from backend.common.futures import TypedFuture
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery


class OffseasonEventHelper:
    @classmethod
    def is_direct_match(cls, tba_event: Event, first_event: Event) -> None:
        return tba_event.key_name == first_event.key_name or (
            tba_event.first_code
            and tba_event.first_code.lower() == first_event.event_short
        )

    @classmethod
    def is_maybe_match(cls, tba_event: Event, first_event: Event) -> bool:
        return (
            tba_event.start_date == first_event.start_date
            and tba_event.end_date == first_event.end_date
            and tba_event.city == first_event.city
            and tba_event.state_prov == first_event.state_prov
        )

    @classmethod
    def categorize_offseasons(
        cls, year: Year, first_events_offseasons: List[Event]
    ) -> Tuple[List[Tuple[Event, Event]], List[Event]]:
        """
        Takes a list of offseason events from FIRST and sorts them in to two groups -
        events that directly or indirectly match TBA events, and events that do not
        match existing TBA events.

        Returns a tuple of events (TBA/FIRST event tuples, new FIRST events)
        """
        year_events_future: TypedFuture[List[Event]] = EventListQuery(
            year
        ).fetch_async()
        year_events = year_events_future.get_result()
        tba_events_offseasons = [e for e in year_events if e.is_offseason]

        matched_events: List[Tuple[Event, Event]] = []
        new_events: List[Event] = []

        for first_event in first_events_offseasons:
            tba_event = next(
                (
                    e
                    for e in tba_events_offseasons
                    if cls.is_direct_match(e, first_event)
                    or cls.is_maybe_match(e, first_event)
                ),
                None,
            )
            if tba_event:
                matched_events.append((tba_event, first_event))
            else:
                new_events.append(first_event)

        return (matched_events, new_events)
