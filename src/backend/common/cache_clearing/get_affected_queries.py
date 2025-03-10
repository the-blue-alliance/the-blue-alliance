from typing import Any, List, Set, Tuple, Type

from google.appengine.ext import ndb

from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.queries import (
    award_query,
    district_query,
    event_details_query,
    event_query,
    insight_query,
    match_query,
    media_query,
    robot_query,
    team_query,
)
from backend.common.queries.database_query import CachedDatabaseQuery

TCacheKeyAndQuery = Tuple[str, Type[CachedDatabaseQuery]]


def _queries_to_cache_keys_and_queries(
    queries: List[CachedDatabaseQuery],
) -> List[TCacheKeyAndQuery]:
    out = []
    for query in queries:
        out.append((query.cache_key, type(query)))
    return out


def _filter(refs: Set[Any]) -> Set[Any]:
    # Default filter() filters zeros, so we can't use it.
    return {r for r in refs if r is not None}


def award_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    event_keys = _filter(affected_refs["event"])
    team_keys = _filter(affected_refs["team_list"])
    years = _filter(affected_refs["year"])
    event_types = _filter(affected_refs["event_type_enum"])
    award_types = _filter(affected_refs["award_type_enum"])

    queries: List[CachedDatabaseQuery] = []
    for event_key in event_keys:
        queries.append(award_query.EventAwardsQuery(event_key.id()))
        for team_key in team_keys:
            queries.append(
                award_query.TeamEventAwardsQuery(team_key.id(), event_key.id())
            )

    for team_key in team_keys:
        queries.append(award_query.TeamAwardsQuery(team_key.id()))
        for year in years:
            queries.append(award_query.TeamYearAwardsQuery(team_key.id(), year))
        for event_type in event_types:
            for award_type in award_types:
                queries.append(
                    award_query.TeamEventTypeAwardsQuery(
                        team_key.id(), event_type, award_type
                    )
                )

    return _queries_to_cache_keys_and_queries(queries)


def event_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    event_keys = _filter(affected_refs["key"])
    years = _filter(affected_refs["year"])
    event_district_keys = _filter(affected_refs["district_key"])

    event_team_keys_future = EventTeam.query(
        EventTeam.event.IN([event_key for event_key in event_keys])  # pyre-ignore[16]
    ).fetch_async(None, keys_only=True)
    events_future = ndb.get_multi_async(event_keys)

    queries: List[CachedDatabaseQuery] = []
    for event_key in event_keys:
        queries.append(event_query.EventQuery(event_key.id()))
        queries.append(event_query.EventDivisionsQuery(event_key.id()))

    for year in years:
        queries.append(event_query.EventListQuery(year))
        queries.append(event_query.RegionalEventsQuery(year))
        queries.append(event_query.ChampionshipEventsAndDivisionsInYearQuery(year))

    for event_district_key in event_district_keys:
        queries.append(event_query.DistrictEventsQuery(event_district_key.id()))

    if event_keys:
        for et_key in event_team_keys_future.get_result():
            team_key = et_key.id().split("_")[1]
            year = int(et_key.id()[:4])
            queries.append(event_query.TeamEventsQuery(team_key))
            queries.append(event_query.TeamYearEventsQuery(team_key, year))
            queries.append(event_query.TeamYearEventTeamsQuery(team_key, year))

    events_with_parents = filter(
        lambda e: e.get_result() is not None
        and e.get_result().parent_event is not None,
        events_future,
    )
    parent_keys = set([e.get_result().parent_event for e in events_with_parents])
    for parent_key in parent_keys:
        queries.append(event_query.EventDivisionsQuery(parent_key.id()))

    return _queries_to_cache_keys_and_queries(queries)


def event_details_updated(
    affected_refs: TAffectedReferences,
) -> List[TCacheKeyAndQuery]:
    event_details_keys = _filter(affected_refs["key"])

    queries: List[CachedDatabaseQuery] = []
    for event_details_key in event_details_keys:
        queries.append(event_details_query.EventDetailsQuery(event_details_key.id()))

    return _queries_to_cache_keys_and_queries(queries)


def match_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    match_keys = _filter(affected_refs["key"])
    event_keys = _filter(affected_refs["event"])
    team_keys = _filter(affected_refs["team_keys"])
    years = _filter(affected_refs["year"])

    queries: List[CachedDatabaseQuery] = []
    for match_key in match_keys:
        queries.append(match_query.MatchQuery(match_key.id()))
        # queries.append(match_query.MatchGdcvDataQuery(match_key.id()))

    for event_key in event_keys:
        queries.append(match_query.EventMatchesQuery(event_key.id()))
        # queries.append(match_query.EventMatchesGdcvDataQuery(event_key.id()))
        for team_key in team_keys:
            queries.append(
                match_query.TeamEventMatchesQuery(team_key.id(), event_key.id())
            )

    for team_key in team_keys:
        for year in years:
            queries.append(match_query.TeamYearMatchesQuery(team_key.id(), year))

    return _queries_to_cache_keys_and_queries(queries)


def media_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    reference_keys = _filter(affected_refs["references"])
    years = _filter(affected_refs["year"])
    media_tags = _filter(affected_refs["media_tag_enum"])

    team_keys = list(filter(lambda x: x.kind() == "Team", reference_keys))
    event_team_keys_future = (
        EventTeam.query(EventTeam.team.IN(team_keys)).fetch_async(  # pyre-ignore[16]
            None, keys_only=True
        )
        if team_keys
        else None
    )

    queries: List[CachedDatabaseQuery] = []
    for reference_key in reference_keys:
        if reference_key.kind() == "Team":
            for year in years:
                queries.append(media_query.TeamYearMediaQuery(reference_key.id(), year))
                for media_tag in media_tags:
                    queries.append(
                        media_query.TeamYearTagMediasQuery(
                            reference_key.id(), year, media_tag
                        )
                    )
            for media_tag in media_tags:
                queries.append(
                    media_query.TeamTagMediasQuery(reference_key.id(), media_tag)
                )
            queries.append(media_query.TeamSocialMediaQuery(reference_key.id()))
        if reference_key.kind() == "Event":
            queries.append(media_query.EventMediasQuery(reference_key.id()))

    if event_team_keys_future:
        for event_team_key in event_team_keys_future.get_result():
            event_key = event_team_key.id().split("_")[0]
            year = int(event_key[:4])
            if year in years:
                queries.append(media_query.EventTeamsMediasQuery(event_key))
                queries.append(media_query.EventTeamsPreferredMediasQuery(event_key))

    return _queries_to_cache_keys_and_queries(queries)


def robot_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    team_keys = _filter(affected_refs["team"])

    queries: List[CachedDatabaseQuery] = []
    for team_key in team_keys:
        queries.append(robot_query.TeamRobotsQuery(team_key.id()))

    return _queries_to_cache_keys_and_queries(queries)


def team_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    team_keys = _filter(affected_refs["key"])

    event_team_keys_future = EventTeam.query(
        EventTeam.team.IN([team_key for team_key in team_keys])  # pyre-ignore[16]
    ).fetch_async(None, keys_only=True)
    district_team_keys_future = DistrictTeam.query(
        DistrictTeam.team.IN([team_key for team_key in team_keys])
    ).fetch_async(None, keys_only=True)

    queries: List[CachedDatabaseQuery] = []
    for team_key in team_keys:
        queries.append(team_query.TeamQuery(team_key.id()))
        page_num = team_query.get_team_page_num(team_key.id())
        queries.append(team_query.TeamListQuery(page_num))

    for et_key in event_team_keys_future.get_result():
        year = int(et_key.id()[:4])
        event_key = et_key.id().split("_")[0]
        page_num = team_query.get_team_page_num(et_key.id().split("_")[1])
        queries.append(team_query.TeamListYearQuery(year, page_num))
        queries.append(team_query.EventTeamsQuery(event_key))
        queries.append(team_query.EventEventTeamsQuery(event_key))

    for dt_key in district_team_keys_future.get_result():
        district_key = dt_key.id().split("_")[0]
        queries.append(team_query.DistrictTeamsQuery(district_key))

    return _queries_to_cache_keys_and_queries(queries)


def eventteam_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    event_keys = _filter(affected_refs["event"])
    team_keys = _filter(affected_refs["team"])
    years = _filter(affected_refs["year"])

    queries: List[CachedDatabaseQuery] = []
    for team_key in team_keys:
        queries.append(event_query.TeamEventsQuery(team_key.id()))
        queries.append(team_query.TeamParticipationQuery(team_key.id()))
        page_num = team_query.get_team_page_num(team_key.id())
        for year in years:
            queries.append(event_query.TeamYearEventsQuery(team_key.id(), year))
            queries.append(event_query.TeamYearEventTeamsQuery(team_key.id(), year))
            queries.append(team_query.TeamListYearQuery(year, page_num))

    for event_key in event_keys:
        queries.append(team_query.EventTeamsQuery(event_key.id()))
        queries.append(team_query.EventEventTeamsQuery(event_key.id()))
        queries.append(media_query.EventTeamsMediasQuery(event_key.id()))
        queries.append(media_query.EventTeamsPreferredMediasQuery(event_key.id()))

    return _queries_to_cache_keys_and_queries(queries)


def districtteam_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    district_keys = _filter(affected_refs["district_key"])
    team_keys = _filter(affected_refs["team"])

    queries: List[CachedDatabaseQuery] = []
    for district_key in district_keys:
        queries.append(team_query.DistrictTeamsQuery(district_key.id()))

    for team_key in team_keys:
        queries.append(district_query.TeamDistrictsQuery(team_key.id()))

    return _queries_to_cache_keys_and_queries(queries)


def regionalpoolteam_updated(
    affected_refs: TAffectedReferences,
) -> List[TCacheKeyAndQuery]:
    years = _filter(affected_refs["year"])

    queries: List[CachedDatabaseQuery] = []
    for year in years:
        queries.append(team_query.RegionalTeamsQuery(year))
    return _queries_to_cache_keys_and_queries(queries)


def regional_champs_pool_updated(
    affected_refs: TAffectedReferences,
) -> List[TCacheKeyAndQuery]:
    years = _filter(affected_refs["year"])

    queries: List[CachedDatabaseQuery] = []
    for year in years:
        queries.append(team_query.RegionalTeamsQuery(year))
    return _queries_to_cache_keys_and_queries(queries)


def district_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    years = _filter(affected_refs["year"])
    district_abbrevs = _filter(affected_refs["abbreviation"])
    district_keys = _filter(affected_refs["key"])

    district_team_keys_future = DistrictTeam.query(
        DistrictTeam.district_key.IN(list(district_keys))
    ).fetch_async(None, keys_only=True)
    district_event_keys_future = Event.query(
        Event.district_key.IN(list(district_keys))  # pyre-ignore[16]
    ).fetch_async(keys_only=True)

    queries: List[CachedDatabaseQuery] = []
    for year in years:
        queries.append(district_query.DistrictsInYearQuery(year))

    for abbrev in district_abbrevs:
        queries.append(district_query.DistrictHistoryQuery(abbrev))

    for key in district_keys:
        queries.append(district_query.DistrictQuery(key.id()))

    for dt_key in district_team_keys_future.get_result():
        team_key = dt_key.id().split("_")[1]
        queries.append(district_query.TeamDistrictsQuery(team_key))

    # Necessary because APIv3 Event models include the District model
    affected_event_refs = {
        "key": set(),
        "year": set(),
        "district_key": district_keys,
    }
    for event_key in district_event_keys_future.get_result():
        affected_event_refs["key"].add(event_key)
        affected_event_refs["year"].add(int(event_key.id()[:4]))

    return _queries_to_cache_keys_and_queries(queries) + event_updated(
        affected_event_refs
    )


def insight_updated(affected_refs: TAffectedReferences) -> List[TCacheKeyAndQuery]:
    years = _filter(affected_refs["year"])

    queries: List[CachedDatabaseQuery] = []
    for year in years:
        queries.append(insight_query.InsightsLeaderboardsYearQuery(year))
        queries.append(insight_query.InsightsNotablesYearQuery(year))

    return _queries_to_cache_keys_and_queries(queries)
