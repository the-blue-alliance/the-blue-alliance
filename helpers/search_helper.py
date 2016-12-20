from collections import defaultdict
from google.appengine.api import search

from consts.award_type import AwardType
from consts.event_type import EventType
from database.award_query import TeamAwardsQuery
from database.event_query import TeamEventsQuery


class SearchHelper(object):
    EVENT_LOCATION_INDEX = 'eventLocation'
    TEAM_LOCATION_INDEX = 'teamLocation'
    TEAM_YEAR_INDEX = 'teamYear'

    @classmethod
    def update_event_location_index(cls, event):
        if event.normalized_location and event.normalized_location.lat_lng:
            fields = [
                search.NumberField(name='year', value=event.year),
                search.GeoField(name='location', value=search.GeoPoint(
                    event.normalized_location.lat_lng.lat,
                    event.normalized_location.lat_lng.lon))
            ]
            search.Index(name="eventLocation").put(
                search.Document(doc_id=event.key.id(), fields=fields))

    @classmethod
    def remove_event_location_index(cls, event):
        search.Index(name=EVENT_LOCATION_INDEX).delete(event.key.id())

    @classmethod
    def update_team_location_index(cls, team):
        if team.normalized_location and team.normalized_location.lat_lng:
            fields = [
                search.GeoField(name='location', value=search.GeoPoint(
                    team.normalized_location.lat_lng.lat,
                    team.normalized_location.lat_lng.lon))
            ]
            search.Index(name=cls.TEAM_LOCATION_INDEX).put(
                search.Document(doc_id=team.key.id(), fields=fields))

    @classmethod
    def remove_team_location_index(cls, team):
        search.Index(name=TEAM_LOCATION_INDEX).delete(team.key.id())

    @classmethod
    def update_team_year_index(cls, team):
        awards_future = TeamAwardsQuery(team.key.id()).fetch_async()
        events_future = TeamEventsQuery(team.key.id()).fetch_async()

        events_by_year = defaultdict(list)
        for event in events_future.get_result():
            events_by_year[event.year].append(event)

        awards_by_year = defaultdict(list)
        for award in awards_future.get_result():
            awards_by_year[award.year].append(award)

        # General stuff that's the same for all years
        same_fields = [
            search.NumberField(name='number', value=team.team_number),
            search.TextField(name='name', value=team.name),
            search.TextField(name='nickname', value=team.nickname)
        ]
        if team.normalized_location and team.normalized_location.lat_lng:
            same_fields += [
                search.GeoField(name='location', value=search.GeoPoint(
                    team.normalized_location.lat_lng.lat,
                    team.normalized_location.lat_lng.lon))
            ]

        # Construct overall and year specific fields
        overall_fields = same_fields + [search.NumberField(name='year', value=0)]
        overall_event_types = set()
        overall_event_award_types = set()
        overall_bb_count = 0
        overall_divwin_count = 0
        overall_cmpwin_count = 0
        for year, events in events_by_year.items():
            year_fields = same_fields + [search.NumberField(name='year', value=year)]

            # Events
            year_event_types = set()
            for event in events:
                if event.event_type_enum not in overall_event_types:
                    overall_fields += [search.AtomField(name='event_type', value=str(event.event_type_enum))]
                    overall_event_types.add(event.event_type_enum)
                if event.event_type_enum not in year_event_types:
                    year_fields += [search.AtomField(name='event_type', value=str(event.event_type_enum))]
                    year_event_types.add(event.event_type_enum)

            # Awards
            year_event_award_types = set()
            year_bb_count = 0
            year_divwin_count = 0
            year_cmpwin_count = 0
            for award in awards_by_year.get(year, []):
                ea_type = 'e{} a{}'.format(award.event_type_enum, award.award_type_enum)
                if ea_type not in overall_event_award_types:
                    overall_fields += [search.TextField(name='event_award_type', value=ea_type)]
                    overall_event_award_types.add(ea_type)
                if ea_type not in year_event_award_types:
                    year_fields += [search.TextField(name='event_award_type', value=ea_type)]
                    year_event_award_types.add(ea_type)
                if award.award_type_enum in AwardType.BLUE_BANNER_AWARDS:
                    overall_bb_count += 1
                    year_bb_count += 1
                if award.award_type_enum == AwardType.WINNER:
                    if award.event_type_enum == EventType.CMP_DIVISION:
                        overall_divwin_count += 1
                        year_divwin_count += 1
                    elif award.event_type_enum == EventType.CMP_FINALS:
                        overall_cmpwin_count += 1
                        year_cmpwin_count += 1
            year_fields += [
                search.NumberField(name='bb_count', value=year_bb_count),
                search.NumberField(name='divwin_count', value=year_divwin_count),
                search.NumberField(name='cmpwin_count', value=year_cmpwin_count),
            ]

            # Put year index
            search.Index(name=cls.TEAM_YEAR_INDEX).put(
                search.Document(doc_id='{}_{}'.format(team.key.id(), year), fields=year_fields))

        overall_fields += [
            search.NumberField(name='bb_count', value=overall_bb_count),
            search.NumberField(name='divwin_count', value=overall_divwin_count),
            search.NumberField(name='cmpwin_count', value=overall_cmpwin_count),
        ]

        # Put overall index
        search.Index(name=cls.TEAM_YEAR_INDEX).put(
            search.Document(doc_id='{}_0'.format(team.key.id()), fields=overall_fields))
