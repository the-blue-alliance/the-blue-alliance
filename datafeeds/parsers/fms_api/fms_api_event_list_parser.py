import datetime

from consts.district_type import DistrictType
from consts.event_type import EventType
from helpers.event_helper import EventHelper

from models.event import Event


class FMSAPIEventListParser(object):

    DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, season):
        self.season = int(season)

    def parse(self, response):
        events = []
        for event in response['Events']:
            code = event['code'].lower()
            key = "{}{}".format(self.season, code)
            name = event['name']
            short_name = EventHelper.getShortName(name)
            event_type = EventHelper.parseEventType(event['type'])
            district_enum = EventHelper.parseDistrictName(event['districtCode'].lower()) if event['districtCode'] else DistrictType.NO_DISTRICT
            venue = event['venue']
            location = "{}, {}, {}".format(event['city'], event['stateprov'], event['country'])
            start = datetime.datetime.strptime(event['dateStart'], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event['dateEnd'], self.DATE_FORMAT_STR)

            # TODO read timezone from API

            # Do not read in CMP divisions, we'll add those manually
            if event_type not in EventType.NON_CMP_EVENT_TYPES:
                continue

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
                event_district_enum=district_enum
            ))
        return events
