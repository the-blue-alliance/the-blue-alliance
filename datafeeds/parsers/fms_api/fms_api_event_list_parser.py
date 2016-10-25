import datetime
import logging

from consts.district_type import DistrictType
from consts.event_type import EventType
from helpers.event_helper import EventHelper

from models.event import Event


class FMSAPIEventListParser(object):

    DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S"

    EVENT_TYPES = {
        'regional': EventType.REGIONAL,
        'districtevent': EventType.DISTRICT,
        'districtchampionship': EventType.DISTRICT_CMP,
        'championshipsubdivision': EventType.CMP_DIVISION,
        'championship': EventType.CMP_FINALS,
        'offseason': EventType.OFFSEASON,
    }

    EVENT_CODE_EXCEPTIONS = {
        'archimedes': ('arc', 'Archimedes'),  # (code, short_name)
        'carson': ('cars', 'Carson'),
        'carver': ('carv', 'Carver'),
        'curie': ('cur', 'Curie'),
        'daly': ('dal', 'Daly'),
        'darwin': ('dar', 'Darwin'),
        'galileo': ('gal', 'Galileo'),
        'hopper': ('hop', 'Hopper'),
        'newton': ('new', 'Newton'),
        'roebling': ('roe', 'Roebling'),
        'tesla': ('tes', 'Tesla'),
        'turing': ('tur', 'Turing'),
        'cmp': ('cmp', 'Einstein'),
        'cmpmo': ('cmpmo', 'Einstein (St. Louis)'),
        'cmptx': ('cmptx', 'Einstein (Houston)'),
    }

    EINSTEIN_CODES = {'cmp', 'cmpmo', 'cmptx'}

    def __init__(self, season):
        self.season = int(season)

    def parse(self, response):
        events = []
        for event in response['Events']:
            code = event['code'].lower()
            event_type = self.EVENT_TYPES.get(event['type'].lower(), None)
            if event_type is None:
                logging.warn("Event type '{}' not recognized!".format(event['type']))
                continue
            name = event['name']
            short_name = EventHelper.getShortName(name)
            district_enum = EventHelper.parseDistrictName(event['districtCode'].lower()) if event['districtCode'] else DistrictType.NO_DISTRICT
            venue = event['venue']
            city = event['city']
            state_prov = event['stateprov']
            country = event['country']
            start = datetime.datetime.strptime(event['dateStart'], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event['dateEnd'], self.DATE_FORMAT_STR)

            # TODO read timezone from API

            # Special cases for champs
            if code in self.EVENT_CODE_EXCEPTIONS:
                code, short_name = self.EVENT_CODE_EXCEPTIONS[code]
                if code in self.EINSTEIN_CODES:
                    name = '{} Field'.format(short_name)
                    start = end.replace(hour=0, minute=0, second=0, microsecond=0)  # Set to beginning of last day
                else:  # Divisions
                    name = '{} Division'.format(short_name)

            events.append(Event(
                id="{}{}".format(self.season, code),
                name=name,
                short_name=short_name,
                event_short=code,
                event_type_enum=event_type,
                official=True,
                start_date=start,
                end_date=end,
                venue=venue,
                city=city,
                state_prov=state_prov,
                country=country,
                venue_address=None,  # FIRST API doesn't provide detailed venue address
                year=self.season,
                event_district_enum=district_enum
            ))
        return events
