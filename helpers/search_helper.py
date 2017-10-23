from collections import defaultdict
from google.appengine.api import search

from consts.award_type import AwardType
from consts.event_type import EventType
from consts.media_type import MediaType
from database.award_query import TeamAwardsQuery
from database.event_query import TeamEventsQuery
from database.match_query import TeamYearMatchesQuery
from database.media_query import TeamMediaQuery
from database.team_query import TeamParticipationQuery


class SearchHelper(object):
    EVENT_LOCATION_INDEX = 'eventLocation'
    TEAM_LOCATION_INDEX = 'teamLocation'
    TEAM_AWARDS_INDEX = 'teamAwards'

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
        search.Index(name=cls.EVENT_LOCATION_INDEX).delete(event.key.id())

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
        search.Index(name=cls.TEAM_LOCATION_INDEX).delete(team.key.id())

    @classmethod
    def update_team_awards_index(cls, team):
        awards_future = TeamAwardsQuery(team.key.id()).fetch_async()
        events_future = TeamEventsQuery(team.key.id()).fetch_async()
        medias_future = TeamMediaQuery(team.key.id()).fetch_async()

        events_by_year = defaultdict(list)
        for event in events_future.get_result():
            events_by_year[event.year].append(event)
            event.prep_details()  # For rankings

        awards_by_event = defaultdict(list)
        for award in awards_future.get_result():
            awards_by_event[award.event.id()].append(award)

        medias_by_year = defaultdict(list)
        for media in medias_future.get_result():
            medias_by_year[media.year].append(media)

        # General stuff that's the same for indexes
        partial_fields = [
            search.NumberField(name='number', value=team.team_number),
            search.TextField(name='name', value=team.name),
            search.TextField(name='nickname', value=team.nickname)
        ]

        # field_counts = defaultdict(int)
        for year, events in events_by_year.items():
            year_matches_future = TeamYearMatchesQuery(team.key.id(), year).fetch_async()
            qual_seeds = defaultdict(int)
            comp_levels = defaultdict(int)
            year_awards = set()
            for event in events:
                if event.event_type_enum not in EventType.SEASON_EVENT_TYPES:
                    continue

                if event.rankings:
                    for row in event.rankings:
                        if str(row[1]) == str(team.team_number):
                            seed = int(row[0])
                            for s in xrange(seed, 9):
                                qual_seeds[s] += 1
                            break

                awards = awards_by_event.get(event.key.id(), [])
                award_types = set([a.award_type_enum for a in awards])
                for award_type in award_types:
                    if award_type in AwardType.SEARCHABLE:
                        year_awards.add(award_type)
                    if award_type == AwardType.WINNER:
                        comp_levels['win'] += 1

            event_levels = defaultdict(set)
            for match in year_matches_future.get_result():
                if match.comp_level in {'sf', 'f'} and match.comp_level not in event_levels[match.event.id()]:
                    comp_levels[match.comp_level] += 1
                event_levels[match.event.id()].add(match.comp_level)

            has_cad = False
            for media in medias_by_year[year]:
                if media.media_type_enum in MediaType.robot_types:
                    has_cad = True
                    break

            fields = partial_fields + [
                search.AtomField(name='award', value=str(award)) for award in year_awards
            ] + [search.NumberField(name='year', value=year)]

            if comp_levels:
                for level, count in comp_levels.items():
                    fields += [search.NumberField(name='comp_level_{}'.format(level), value=count)]

            if qual_seeds:
                for seed, count in qual_seeds.items():
                    fields += [search.NumberField(name='seed_{}'.format(seed), value=count)]

            if has_cad:
                fields += [
                    search.NumberField(name='has_cad', value=1)
                ]

            search.Index(name=cls.TEAM_AWARDS_INDEX).put(
                search.Document(doc_id='{}_{}'.format(team.key.id(), year), fields=fields))
