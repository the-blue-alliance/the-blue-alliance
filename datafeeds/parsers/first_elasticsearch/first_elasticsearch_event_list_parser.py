import datetime

from consts.event_type import EventType
from helpers.event_helper import EventHelper

from models.event import Event


class FIRSTElasticSearchEventListParser(object):
    DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S"
    TYPES_TO_SKIP = EventType.CMP_EVENT_TYPES.union(set([EventType.UNLABLED]))

    def __init__(self, season):
        self.season = int(season)

    def parse(self, response):
        events = []
        for event in response['hits']['hits']:
            first_eid = event['_id']
            event = event['_source']

            event_type = EventHelper.parseEventType(event['event_subtype'])
            if event_type in self.TYPES_TO_SKIP:
                continue

            code = event['event_code'].lower()
            key = "{}{}".format(self.season, code)
            name = event['event_name']
            short_name = EventHelper.getShortName(name)
            district_enum = EventHelper.getDistrictFromEventName(name)
            venue = event['event_venue']
            location = "{}, {}, {}".format(event['event_city'], event['event_stateprov'], event['event_country'])
            start = datetime.datetime.strptime(event['date_start'], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event['date_end'], self.DATE_FORMAT_STR) + datetime.timedelta(hours=23, minutes=59, seconds=59)

            events.append(Event(
                id=key,
                name=name,
                short_name=short_name,
                event_short=code,
                event_type_enum=event_type,
                official=True,
                start_date=start,
                end_date=end,
                venue=venue,
                location=location,
                venue_address="{}, {}".format(venue, location),
                year=self.season,
                event_district_enum=district_enum,
                first_eid=first_eid,
                website=event.get('event_web_url', None)
            ))
        return events
