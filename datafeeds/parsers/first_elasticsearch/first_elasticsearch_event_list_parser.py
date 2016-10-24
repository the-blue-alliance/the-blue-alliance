import datetime
import urlparse

from consts.district_type import DistrictType
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
            if event_type in EventType.DISTRICT_EVENT_TYPES:
                district_enum = EventHelper.getDistrictFromEventName(name)
            else:
                district_enum = DistrictType.NO_DISTRICT
            city = event.get('event_city', None)
            state_prov = event.get('event_stateprov', None)
            country = event.get('event_country', None)
            start = datetime.datetime.strptime(event['date_start'], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event['date_end'], self.DATE_FORMAT_STR) + datetime.timedelta(hours=23, minutes=59, seconds=59)
            venue_address = event['event_venue']
            if 'event_address1' in event and event['event_address1']:
                venue_address += '\n' + event['event_address1']
            if 'event_address2' in event and event['event_address2']:
                venue_address += '\n' + event['event_address2']
            venue_address += '\n{}, {} {}\n{}'.format(event['event_city'], event['event_stateprov'], event['event_postalcode'], event['event_country'])

            raw_website = event.get('event_web_url', None)
            website = urlparse.urlparse(raw_website, 'http').geturl() if raw_website else None

            events.append(Event(
                id=key,
                name=name,
                short_name=short_name,
                event_short=code,
                event_type_enum=event_type,
                official=True,
                start_date=start,
                end_date=end,
                venue=event['event_venue'],
                city=city,
                state_prov=state_prov,
                country=country,
                venue_address=venue_address,
                year=self.season,
                event_district_enum=district_enum,
                first_eid=first_eid,
                website=website
            ))
        return events
