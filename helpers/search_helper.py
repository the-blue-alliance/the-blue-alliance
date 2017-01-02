from collections import defaultdict
from google.appengine.api import search
from itertools import chain, combinations

from consts.award_type import AwardType
from consts.event_type import EventType
from database.award_query import TeamAwardsQuery
from database.event_query import TeamEventsQuery
from database.team_query import TeamParticipationQuery


class SearchHelper(object):
    EVENT_LOCATION_INDEX = 'eventLocation'
    TEAM_LOCATION_INDEX = 'teamLocation'
    TEAM_AWARDS_INDEX = 'teamAwards'
    MAX_AWARDS = 3  # Max number of awards to search for

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
            partial_fields = [
                search.GeoField(name='location', value=search.GeoPoint(
                    team.normalized_location.lat_lng.lat,
                    team.normalized_location.lat_lng.lon))
            ]
            # Teams by year
            for year in TeamParticipationQuery(team.key.id()).fetch():
                fields = partial_fields + [
                    search.NumberField(name='year', value=year)
                ]
                search.Index(name=cls.TEAM_LOCATION_INDEX).put(
                    search.Document(doc_id='{}_{}'.format(team.key.id(), year), fields=fields))
            # Any year
            search.Index(name=cls.TEAM_LOCATION_INDEX).put(
                    search.Document(doc_id=team.key.id(), fields=partial_fields))

    @classmethod
    def remove_team_location_index(cls, team):
        search.Index(name=TEAM_LOCATION_INDEX).delete(team.key.id())

    @classmethod
    def _construct_powerset(cls, l):
        return chain.from_iterable(combinations(l, n) for n in range(1, cls.MAX_AWARDS + 1))

    @classmethod
    def _construct_set_name(cls, award_set):
        return '_'.join(['a{}'.format(a) for a in sorted(award_set)])

    @classmethod
    def update_team_awards_index(cls, team):
        awards_future = TeamAwardsQuery(team.key.id()).fetch_async()
        events_future = TeamEventsQuery(team.key.id()).fetch_async()

        events_by_year = defaultdict(list)
        for event in events_future.get_result():
            events_by_year[event.year].append(event)

        awards_by_event = defaultdict(list)
        for award in awards_future.get_result():
            awards_by_event[award.event.id()].append(award)

        # General stuff that's the same for indexes
        fields = [
            search.NumberField(name='number', value=team.team_number),
            search.TextField(name='name', value=team.name),
            search.TextField(name='nickname', value=team.nickname)
        ]

        field_counts = defaultdict(int)
        overall_awards = set()
        overall_awards_event = defaultdict(set)
        for year, events in events_by_year.items():
            season_awards = set()
            season_awards_event = defaultdict(set)
            for event in events:
                if event.event_type_enum not in EventType.SEASON_EVENT_TYPES:
                    continue

                awards = awards_by_event.get(event.key.id(), [])
                award_types = set([a.award_type_enum for a in awards])
                award_types = filter(lambda a: a in AwardType.SEARCHABLE, award_types)

                # To search by event
                for award_set in cls._construct_powerset(award_types):
                    set_name = cls._construct_set_name(award_set)
                    field_counts['e_{}'.format(set_name)] += 1
                    field_counts['e_{}_y{}'.format(set_name, event.year)] += 1
                    field_counts['e_{}_e{}'.format(set_name, event.event_type_enum)] += 1
                    field_counts['e_{}_e{}_y{}'.format(set_name, event.event_type_enum, event.year)] += 1

                season_awards = season_awards.union(award_types)
                season_awards_event[event.event_type_enum] = season_awards_event[event.event_type_enum].union(award_types)

                overall_awards = overall_awards.union(award_types)
                overall_awards_event[event.event_type_enum] = overall_awards_event[event.event_type_enum].union(award_types)

            # To search by year
            for award_set in cls._construct_powerset(season_awards):
                set_name = cls._construct_set_name(award_set)
                field_counts['s_{}'.format(set_name)] += 1
                field_counts['s_{}_y{}'.format(set_name, year)] += 1

            for event_type, awards in season_awards_event.items():
                for award_set in cls._construct_powerset(awards):
                    set_name = cls._construct_set_name(award_set)
                    field_counts['s_{}_e{}'.format(set_name, event_type)] += 1
                    field_counts['s_{}_e{}_y{}'.format(set_name, event_type, year)] += 1

        # To search overall
        for award_set in cls._construct_powerset(overall_awards):
            set_name = cls._construct_set_name(award_set)
            field_counts['o_{}'.format(set_name)] += 1

        for event_type, awards in overall_awards_event.items():
            for award_set in cls._construct_powerset(awards):
                set_name = cls._construct_set_name(award_set)
                field_counts['o_{}_e{}'.format(set_name, event_type)] += 1

        fields += [search.NumberField(name=field, value=count) for field, count in field_counts.items()]
        search.Index(name=cls.TEAM_AWARDS_INDEX).put(
            search.Document(doc_id='{}'.format(team.key.id()), fields=fields))
