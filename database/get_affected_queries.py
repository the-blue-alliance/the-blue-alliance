from google.appengine.ext import ndb

from database.award_query import EventAwardsQuery, TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery, TeamEventTypeAwardsQuery
from database.district_query import DistrictsInYearQuery, DistrictHistoryQuery, DistrictQuery
from database.event_query import EventQuery, EventListQuery, DistrictEventsQuery, TeamEventsQuery, TeamYearEventsQuery, TeamYearEventTeamsQuery, \
    EventDivisionsQuery
from database.event_details_query import EventDetailsQuery
from database.gdcv_data_query import MatchGdcvDataQuery, EventMatchesGdcvDataQuery
from database.match_query import MatchQuery, EventMatchesQuery, TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamSocialMediaQuery, TeamYearMediaQuery, EventTeamsMediasQuery, EventTeamsPreferredMediasQuery, \
    EventMediasQuery, TeamTagMediasQuery, TeamYearTagMediasQuery
from database.robot_query import TeamRobotsQuery
from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, DistrictTeamsQuery, EventTeamsQuery, EventEventTeamsQuery, TeamParticipationQuery, TeamDistrictsQuery

from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam


def _get_team_page_num(team_key):
    return int(team_key[3:]) / TeamListQuery.PAGE_SIZE


def _filter(refs):
    # Default filter() filters zeros, so we can't use it.
    return [r for r in refs if r is not None]


def award_updated(affected_refs):
    event_keys = _filter(affected_refs['event'])
    team_keys = _filter(affected_refs['team_list'])
    years = _filter(affected_refs['year'])
    event_types = _filter(affected_refs['event_type_enum'])
    award_types = _filter(affected_refs['award_type_enum'])

    queries_and_keys = []
    for event_key in event_keys:
        queries_and_keys.append((EventAwardsQuery(event_key.id())))
        for team_key in team_keys:
            queries_and_keys.append((TeamEventAwardsQuery(team_key.id(), event_key.id())))

    for team_key in team_keys:
        queries_and_keys.append((TeamAwardsQuery(team_key.id())))
        for year in years:
            queries_and_keys.append((TeamYearAwardsQuery(team_key.id(), year)))
        for event_type in event_types:
            for award_type in award_types:
                queries_and_keys.append((TeamEventTypeAwardsQuery(team_key.id(), event_type, award_type)))

    return queries_and_keys


def event_updated(affected_refs):
    event_keys = _filter(affected_refs['key'])
    years = _filter(affected_refs['year'])
    event_district_keys = _filter(affected_refs['district_key'])

    event_team_keys_future = EventTeam.query(EventTeam.event.IN([event_key for event_key in event_keys])).fetch_async(None, keys_only=True)
    events_future = ndb.get_multi_async(event_keys)

    queries_and_keys = []
    for event_key in event_keys:
        queries_and_keys.append((EventQuery(event_key.id())))
        queries_and_keys.append(EventDivisionsQuery(event_key.id()))

    for year in years:
        queries_and_keys.append((EventListQuery(year)))

    for event_district_key in event_district_keys:
        queries_and_keys.append((DistrictEventsQuery(event_district_key.id())))

    if event_keys:
        for et_key in event_team_keys_future.get_result():
            team_key = et_key.id().split('_')[1]
            year = int(et_key.id()[:4])
            queries_and_keys.append((TeamEventsQuery(team_key)))
            queries_and_keys.append((TeamYearEventsQuery(team_key, year)))
            queries_and_keys.append((TeamYearEventTeamsQuery(team_key, year)))

    events_with_parents = filter(lambda e: e.get_result() is not None and e.get_result().parent_event is not None, events_future)
    parent_keys = set([e.get_result().parent_event for e in events_with_parents])
    for parent_key in parent_keys:
        queries_and_keys.append((EventDivisionsQuery(parent_key.id())))

    return queries_and_keys


def event_details_updated(affected_refs):
    event_details_keys = _filter(affected_refs['key'])

    queries_and_keys = []
    for event_details_key in event_details_keys:
        queries_and_keys.append((EventDetailsQuery(event_details_key.id())))

    return queries_and_keys


def match_updated(affected_refs):
    match_keys = _filter(affected_refs['key'])
    event_keys = _filter(affected_refs['event'])
    team_keys = _filter(affected_refs['team_keys'])
    years = _filter(affected_refs['year'])

    queries_and_keys = []
    for match_key in match_keys:
        queries_and_keys.append((MatchQuery(match_key.id())))
        queries_and_keys.append((MatchGdcvDataQuery(match_key.id())))

    for event_key in event_keys:
        queries_and_keys.append((EventMatchesQuery(event_key.id())))
        queries_and_keys.append((EventMatchesGdcvDataQuery(event_key.id())))
        for team_key in team_keys:
            queries_and_keys.append((TeamEventMatchesQuery(team_key.id(), event_key.id())))

    for team_key in team_keys:
        for year in years:
            queries_and_keys.append((TeamYearMatchesQuery(team_key.id(), year)))

    return queries_and_keys


def media_updated(affected_refs):
    reference_keys = _filter(affected_refs['references'])
    years = _filter(affected_refs['year'])
    media_tags = _filter(affected_refs['media_tag_enum'])

    team_keys = filter(lambda x: x.kind() == 'Team', reference_keys)
    event_team_keys_future = EventTeam.query(EventTeam.team.IN(team_keys)).fetch_async(None, keys_only=True) if team_keys else None

    queries_and_keys = []
    for reference_key in reference_keys:
        if reference_key.kind() == 'Team':
            for year in years:
                queries_and_keys.append((TeamYearMediaQuery(reference_key.id(), year)))
                for media_tag in media_tags:
                    queries_and_keys.append((TeamYearTagMediasQuery(reference_key.id(), media_tag, year)))
            for media_tag in media_tags:
                queries_and_keys.append((TeamTagMediasQuery(reference_key.id(), media_tag)))
            queries_and_keys.append((TeamSocialMediaQuery(reference_key.id())))
        if reference_key.kind() == 'Event':
            queries_and_keys.append((EventMediasQuery(reference_key.id())))

    if event_team_keys_future:
        for event_team_key in event_team_keys_future.get_result():
            event_key = event_team_key.id().split('_')[0]
            year = int(event_key[:4])
            if year in years:
                queries_and_keys.append(EventTeamsMediasQuery(event_key))
                queries_and_keys.append(EventTeamsPreferredMediasQuery(event_key))

    return queries_and_keys


def robot_updated(affected_refs):
    team_keys = _filter(affected_refs['team'])

    queries_and_keys = []
    for team_key in team_keys:
        queries_and_keys.append((TeamRobotsQuery(team_key.id())))

    return queries_and_keys


def team_updated(affected_refs):
    team_keys = _filter(affected_refs['key'])

    event_team_keys_future = EventTeam.query(EventTeam.team.IN([team_key for team_key in team_keys])).fetch_async(None, keys_only=True)
    district_team_keys_future = DistrictTeam.query(DistrictTeam.team.IN([team_key for team_key in team_keys])).fetch_async(None, keys_only=True)

    queries_and_keys = []
    for team_key in team_keys:
        queries_and_keys.append((TeamQuery(team_key.id())))
        page_num = _get_team_page_num(team_key.id())
        queries_and_keys.append((TeamListQuery(page_num)))

    for et_key in event_team_keys_future.get_result():
        year = int(et_key.id()[:4])
        event_key = et_key.id().split('_')[0]
        page_num = _get_team_page_num(et_key.id().split('_')[1])
        queries_and_keys.append((TeamListYearQuery(year, page_num)))
        queries_and_keys.append((EventTeamsQuery(event_key)))
        queries_and_keys.append((EventEventTeamsQuery(event_key)))

    for dt_key in district_team_keys_future.get_result():
        district_key = dt_key.id().split('_')[0]
        queries_and_keys.append((DistrictTeamsQuery(district_key)))

    return queries_and_keys


def eventteam_updated(affected_refs):
    event_keys = _filter(affected_refs['event'])
    team_keys = _filter(affected_refs['team'])
    years = _filter(affected_refs['year'])

    queries_and_keys = []
    for team_key in team_keys:
        queries_and_keys.append(TeamEventsQuery(team_key.id()))
        queries_and_keys.append(TeamParticipationQuery(team_key.id()))
        page_num = _get_team_page_num(team_key.id())
        for year in years:
            queries_and_keys.append(TeamYearEventsQuery(team_key.id(), year))
            queries_and_keys.append(TeamYearEventTeamsQuery(team_key.id(), year))
            queries_and_keys.append(TeamListYearQuery(year, page_num))

    for event_key in event_keys:
        queries_and_keys.append(EventTeamsQuery(event_key.id()))
        queries_and_keys.append(EventEventTeamsQuery(event_key.id()))
        queries_and_keys.append(EventTeamsMediasQuery(event_key.id()))
        queries_and_keys.append(EventTeamsPreferredMediasQuery(event_key.id()))

    return queries_and_keys


def districtteam_updated(affected_refs):
    district_keys = _filter(affected_refs['district_key'])
    team_keys = _filter(affected_refs['team'])

    queries_and_keys = []
    for district_key in district_keys:
        queries_and_keys.append(DistrictTeamsQuery(district_key.id()))

    for team_key in team_keys:
        queries_and_keys.append(TeamDistrictsQuery(team_key.id()))

    return queries_and_keys


def district_updated(affected_refs):
    years = _filter(affected_refs['year'])
    district_abbrevs = _filter(affected_refs['abbreviation'])
    district_keys = _filter(affected_refs['key'])

    district_team_keys_future = DistrictTeam.query(DistrictTeam.district_key.IN(list(district_keys))).fetch_async(None, keys_only=True)
    district_event_keys_future = Event.query(Event.district_key.IN(list(district_keys))).fetch_async(keys_only=True)

    queries_and_keys = []
    for year in years:
        queries_and_keys.append(DistrictsInYearQuery(year))

    for abbrev in district_abbrevs:
        queries_and_keys.append(DistrictHistoryQuery(abbrev))

    for key in district_keys:
        queries_and_keys.append(DistrictQuery(key.id()))

    for dt_key in district_team_keys_future.get_result():
        team_key = dt_key.id().split('_')[1]
        queries_and_keys.append(TeamDistrictsQuery(team_key))

    # Necessary because APIv3 Event models include the District model
    affected_event_refs = {
        'key': set(),
        'year': set(),
        'district_key': district_keys,
    }
    for event_key in district_event_keys_future.get_result():
        affected_event_refs['key'].add(event_key)
        affected_event_refs['year'].add(int(event_key.id()[:4]))
    queries_and_keys += event_updated(affected_event_refs)

    return queries_and_keys
