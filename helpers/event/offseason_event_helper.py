import logging

from consts.event_type import EventType
from database.event_query import EventListQuery


class OffseasonEventHelper(object):

    @classmethod
    def is_direct_match(cls, tba_event, first_event):
        return tba_event.key_name == first_event.key_name or \
               (tba_event.first_code and tba_event.first_code.lower() == first_event.event_short)

    @classmethod
    def is_maybe_match(cls, tba_event, first_event):
        return tba_event.start_date == first_event.start_date \
               and tba_event.end_date == first_event.end_date \
               and tba_event.city == first_event.city \
               and tba_event.state_prov == first_event.state_prov

    @classmethod
    def categorize_offseasons(cls, year, first_events):
        """
        Takes a list of sync-enabled offseasons from FIRST and sorts them
        Returns a tuple of events (linked to TBA, candidates to link, new)
        """
        year_events_future = EventListQuery(year).fetch_async()
        year_events = year_events_future.get_result()
        year_offseasons = [e for e in year_events if e.event_type_enum == EventType.OFFSEASON or e.event_type_enum == EventType.PRESEASON]

        matched_events = []
        likely_matched_events = []
        new_events = []

        logging.info("Categorizing {} events from FIRST".format(len(first_events)))
        for event in first_events:
            matching_tba_event_by_key = next((e for e in year_offseasons if cls.is_direct_match(e, event)), None)
            if matching_tba_event_by_key:
                matched_events.append((matching_tba_event_by_key, event))
                continue

            likely_match = next((e for e in year_offseasons if cls.is_maybe_match(e, event)), None)
            if likely_match:
                likely_matched_events.append((likely_match, event))
                continue

            new_events.append(event)

        return (matched_events, likely_matched_events, new_events)
