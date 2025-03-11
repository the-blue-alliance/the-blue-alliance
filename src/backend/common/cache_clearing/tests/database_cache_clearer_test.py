import unittest

import pytest
from google.appengine.ext import ndb

from backend.common.cache_clearing import get_affected_queries
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team
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


@pytest.mark.usefixtures("ndb_context")
class TestDatabaseCacheClearer(unittest.TestCase):
    def setUp(self) -> None:
        eventteam_2015casj_frc254 = EventTeam(
            id="2015casj_frc254",
            event=ndb.Key(Event, "2015casj"),
            team=ndb.Key(Team, "frc254"),
            year=2015,
        )

        eventteam_2015cama_frc604 = EventTeam(
            id="2015cama_frc604",
            event=ndb.Key(Event, "2015cama"),
            team=ndb.Key(Team, "frc604"),
            year=2015,
        )

        eventteam_2010cama_frc604 = EventTeam(
            id="2010cama_frc604",
            event=ndb.Key(Event, "2010cama"),
            team=ndb.Key(Team, "frc604"),
            year=2010,
        )

        eventteam_2016necmp_frc125 = EventTeam(
            id="2016necmp_frc125",
            event=ndb.Key(Event, "2016necmp"),
            team=ndb.Key(Team, "frc125"),
            year=2016,
        )

        eventteam_2015casj_frc254.put()
        eventteam_2015cama_frc604.put()
        eventteam_2010cama_frc604.put()
        eventteam_2016necmp_frc125.put()

        districtteam_2015fim_frc254 = DistrictTeam(
            id="2015fim_frc254",
            district_key=ndb.Key(District, "2015fim"),
            team=ndb.Key(Team, "frc254"),
            year=2015,
        )

        districtteam_2015mar_frc604 = DistrictTeam(
            id="2015mar_frc604",
            district_key=ndb.Key(District, "2015mar"),
            team=ndb.Key(Team, "frc604"),
            year=2015,
        )

        districtteam_2016ne_frc604 = DistrictTeam(
            id="2016ne_frc604",
            district_key=ndb.Key(District, "2016ne"),
            team=ndb.Key(Team, "frc604"),
            year=2016,
        )

        districtteam_2015fim_frc254.put()
        districtteam_2015mar_frc604.put()
        districtteam_2016ne_frc604.put()

        district_2015ne = District(
            id="2015ne",
            year=2015,
            abbreviation="ne",
        )

        district_2016chs = District(
            id="2016chs",
            year=2016,
            abbreviation="chs",
        )
        district_2015ne.put()
        district_2016chs.put()

        event_2016necmp = Event(
            id="2016necmp",
            year=2016,
            district_key=ndb.Key(District, "2016ne"),
            event_short="necmp",
            event_type_enum=EventType.DISTRICT_CMP,
        )
        event_2016necmp.put()

        event_2015casj = Event(
            id="2015casj",
            year=2015,
            event_short="casj",
            event_type_enum=EventType.REGIONAL,
            parent_event=ndb.Key(Event, "2015cafoo"),
        )
        event_2015casj.put()

    def test_award_updated(self) -> None:
        affected_refs = {
            "event": {ndb.Key(Event, "2015casj"), ndb.Key(Event, "2015cama")},
            "team_list": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
            "year": {2014, 2015},
            "event_type_enum": {EventType.REGIONAL, EventType.DISTRICT},
            "award_type_enum": {AwardType.WINNER, AwardType.CHAIRMANS},
        }
        cache_keys = {q[0] for q in get_affected_queries.award_updated(affected_refs)}

        expected_keys = {
            award_query.EventAwardsQuery("2015casj").cache_key,
            award_query.EventAwardsQuery("2015cama").cache_key,
            award_query.TeamAwardsQuery("frc254").cache_key,
            award_query.TeamAwardsQuery("frc604").cache_key,
            award_query.TeamYearAwardsQuery("frc254", 2014).cache_key,
            award_query.TeamYearAwardsQuery("frc254", 2015).cache_key,
            award_query.TeamYearAwardsQuery("frc604", 2014).cache_key,
            award_query.TeamYearAwardsQuery("frc604", 2015).cache_key,
            award_query.TeamEventAwardsQuery("frc254", "2015casj").cache_key,
            award_query.TeamEventAwardsQuery("frc254", "2015cama").cache_key,
            award_query.TeamEventAwardsQuery("frc604", "2015casj").cache_key,
            award_query.TeamEventAwardsQuery("frc604", "2015cama").cache_key,
        }

        for team_key in ["frc254", "frc604"]:
            for event_type in [EventType.REGIONAL, EventType.DISTRICT]:
                for award_type in [AwardType.WINNER, AwardType.CHAIRMANS]:
                    expected_keys.add(
                        award_query.TeamEventTypeAwardsQuery(
                            team_key, event_type, award_type
                        ).cache_key
                    )

        assert cache_keys == expected_keys

    def test_event_updated(self) -> None:
        affected_refs = {
            "key": {ndb.Key(Event, "2015casj"), ndb.Key(Event, "2015cama")},
            "year": {2014, 2015},
            "district_key": {
                ndb.Key(District, "2015fim"),
                ndb.Key(District, "2014mar"),
            },
        }
        cache_keys = {q[0] for q in get_affected_queries.event_updated(affected_refs)}

        assert cache_keys == {
            event_query.EventQuery("2015casj").cache_key,
            event_query.EventQuery("2015cama").cache_key,
            event_query.EventListQuery(2014).cache_key,
            event_query.EventListQuery(2015).cache_key,
            event_query.DistrictEventsQuery("2015fim").cache_key,
            event_query.DistrictEventsQuery("2014mar").cache_key,
            event_query.TeamEventsQuery("frc254").cache_key,
            event_query.TeamEventsQuery("frc604").cache_key,
            event_query.TeamYearEventsQuery("frc254", 2015).cache_key,
            event_query.TeamYearEventsQuery("frc604", 2015).cache_key,
            event_query.TeamYearEventTeamsQuery("frc254", 2015).cache_key,
            event_query.TeamYearEventTeamsQuery("frc604", 2015).cache_key,
            event_query.EventDivisionsQuery("2015casj").cache_key,
            event_query.EventDivisionsQuery("2015cama").cache_key,
            event_query.EventDivisionsQuery("2015cafoo").cache_key,
            event_query.RegionalEventsQuery(2014).cache_key,
            event_query.RegionalEventsQuery(2015).cache_key,
            event_query.ChampionshipEventsAndDivisionsInYearQuery(2014).cache_key,
            event_query.ChampionshipEventsAndDivisionsInYearQuery(2015).cache_key,
        }

    def test_event_details_updated(self) -> None:
        affected_refs = {
            "key": {
                ndb.Key(EventDetails, "2015casj"),
                ndb.Key(EventDetails, "2015cama"),
            },
        }
        cache_keys = {
            q[0] for q in get_affected_queries.event_details_updated(affected_refs)
        }

        assert cache_keys == {
            event_details_query.EventDetailsQuery("2015casj").cache_key,
            event_details_query.EventDetailsQuery("2015cama").cache_key,
        }

    def test_match_updated(self) -> None:
        affected_refs = {
            "key": {ndb.Key(Match, "2015casj_qm1"), ndb.Key(Match, "2015casj_qm2")},
            "event": {ndb.Key(Event, "2015casj"), ndb.Key(Event, "2015cama")},
            "team_keys": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
            "year": {2014, 2015},
        }
        cache_keys = {q[0] for q in get_affected_queries.match_updated(affected_refs)}

        assert cache_keys == {
            match_query.MatchQuery("2015casj_qm1").cache_key,
            match_query.MatchQuery("2015casj_qm2").cache_key,
            # self.assertTrue(match_query.MatchGdcvDataQuery('2015casj_qm1').cache_key in cache_keys)
            # self.assertTrue(match_query.MatchGdcvDataQuery('2015casj_qm2').cache_key in cache_keys)
            match_query.EventMatchesQuery("2015casj").cache_key,
            match_query.EventMatchesQuery("2015cama").cache_key,
            # self.assertTrue(match_query.EventMatchesGdcvDataQuery('2015casj').cache_key in cache_keys)
            # self.assertTrue(match_query.EventMatchesGdcvDataQuery('2015cama').cache_key in cache_keys)
            match_query.TeamEventMatchesQuery("frc254", "2015casj").cache_key,
            match_query.TeamEventMatchesQuery("frc254", "2015cama").cache_key,
            match_query.TeamEventMatchesQuery("frc604", "2015casj").cache_key,
            match_query.TeamEventMatchesQuery("frc604", "2015cama").cache_key,
            match_query.TeamYearMatchesQuery("frc254", 2014).cache_key,
            match_query.TeamYearMatchesQuery("frc254", 2015).cache_key,
            match_query.TeamYearMatchesQuery("frc604", 2014).cache_key,
            match_query.TeamYearMatchesQuery("frc604", 2015).cache_key,
        }

    def test_media_updated_team(self) -> None:
        affected_refs = {
            "references": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
            "year": {2014, 2015},
            "media_tag_enum": {MediaTag.CHAIRMANS_ESSAY, MediaTag.CHAIRMANS_VIDEO},
        }
        cache_keys = {q[0] for q in get_affected_queries.media_updated(affected_refs)}

        assert cache_keys == {
            media_query.TeamYearMediaQuery("frc254", 2014).cache_key,
            media_query.TeamYearMediaQuery("frc254", 2015).cache_key,
            media_query.TeamSocialMediaQuery("frc254").cache_key,
            media_query.TeamYearMediaQuery("frc604", 2014).cache_key,
            media_query.TeamYearMediaQuery("frc604", 2015).cache_key,
            media_query.TeamSocialMediaQuery("frc604").cache_key,
            media_query.EventTeamsMediasQuery("2015cama").cache_key,
            media_query.EventTeamsMediasQuery("2015casj").cache_key,
            media_query.EventTeamsPreferredMediasQuery("2015cama").cache_key,
            media_query.EventTeamsPreferredMediasQuery("2015casj").cache_key,
            media_query.TeamTagMediasQuery(
                "frc254", MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
            media_query.TeamTagMediasQuery(
                "frc254", MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamTagMediasQuery(
                "frc604", MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamTagMediasQuery(
                "frc604", MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc254", 2014, MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc254", 2014, MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc254", 2015, MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc254", 2015, MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc604", 2014, MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc604", 2014, MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc604", 2015, MediaTag.CHAIRMANS_VIDEO
            ).cache_key,
            media_query.TeamYearTagMediasQuery(
                "frc604", 2015, MediaTag.CHAIRMANS_ESSAY
            ).cache_key,
        }

    def test_media_updated_event(self) -> None:
        affected_refs = {
            "references": {ndb.Key(Event, "2016necmp")},
            "year": {2016},
            "media_tag_enum": {None, None},
        }
        cache_keys = {q[0] for q in get_affected_queries.media_updated(affected_refs)}

        assert cache_keys == {
            media_query.EventMediasQuery("2016necmp").cache_key,
        }

    def test_robot_updated(self) -> None:
        affected_refs = {
            "team": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
        }
        cache_keys = {q[0] for q in get_affected_queries.robot_updated(affected_refs)}

        assert cache_keys == {
            robot_query.TeamRobotsQuery("frc254").cache_key,
            robot_query.TeamRobotsQuery("frc604").cache_key,
        }

    def test_team_updated(self) -> None:
        affected_refs = {
            "key": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
        }
        cache_keys = {q[0] for q in get_affected_queries.team_updated(affected_refs)}

        assert cache_keys == {
            team_query.TeamQuery("frc254").cache_key,
            team_query.TeamQuery("frc604").cache_key,
            team_query.TeamListQuery(0).cache_key,
            team_query.TeamListQuery(1).cache_key,
            team_query.TeamListYearQuery(2015, 0).cache_key,
            team_query.TeamListYearQuery(2015, 1).cache_key,
            team_query.TeamListYearQuery(2010, 1).cache_key,
            team_query.DistrictTeamsQuery("2015fim").cache_key,
            team_query.DistrictTeamsQuery("2015mar").cache_key,
            team_query.DistrictTeamsQuery("2016ne").cache_key,
            team_query.EventTeamsQuery("2015casj").cache_key,
            team_query.EventTeamsQuery("2015cama").cache_key,
            team_query.EventTeamsQuery("2010cama").cache_key,
            team_query.EventEventTeamsQuery("2015casj").cache_key,
            team_query.EventEventTeamsQuery("2015cama").cache_key,
            team_query.EventEventTeamsQuery("2010cama").cache_key,
        }

    def test_eventteam_updated(self) -> None:
        affected_refs = {
            "event": {ndb.Key(Event, "2015casj"), ndb.Key(Event, "2015cama")},
            "team": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
            "year": {2014, 2015},
        }
        cache_keys = {
            q[0] for q in get_affected_queries.eventteam_updated(affected_refs)
        }

        assert cache_keys == {
            event_query.TeamEventsQuery("frc254").cache_key,
            event_query.TeamEventsQuery("frc604").cache_key,
            team_query.TeamParticipationQuery("frc254").cache_key,
            team_query.TeamParticipationQuery("frc604").cache_key,
            event_query.TeamYearEventsQuery("frc254", 2014).cache_key,
            event_query.TeamYearEventsQuery("frc254", 2015).cache_key,
            event_query.TeamYearEventsQuery("frc604", 2014).cache_key,
            event_query.TeamYearEventsQuery("frc604", 2015).cache_key,
            event_query.TeamYearEventTeamsQuery("frc254", 2014).cache_key,
            event_query.TeamYearEventTeamsQuery("frc254", 2015).cache_key,
            event_query.TeamYearEventTeamsQuery("frc604", 2014).cache_key,
            event_query.TeamYearEventTeamsQuery("frc604", 2015).cache_key,
            team_query.TeamListYearQuery(2014, 0).cache_key,
            team_query.TeamListYearQuery(2014, 1).cache_key,
            team_query.TeamListYearQuery(2015, 0).cache_key,
            team_query.TeamListYearQuery(2015, 1).cache_key,
            team_query.EventTeamsQuery("2015casj").cache_key,
            team_query.EventTeamsQuery("2015cama").cache_key,
            team_query.EventEventTeamsQuery("2015casj").cache_key,
            team_query.EventEventTeamsQuery("2015cama").cache_key,
            media_query.EventTeamsMediasQuery("2015cama").cache_key,
            media_query.EventTeamsMediasQuery("2015casj").cache_key,
            media_query.EventTeamsPreferredMediasQuery("2015cama").cache_key,
            media_query.EventTeamsPreferredMediasQuery("2015casj").cache_key,
        }

    def test_districtteam_updated(self) -> None:
        affected_refs = {
            "district_key": {
                ndb.Key(District, "2015fim"),
                ndb.Key(District, "2015mar"),
            },
            "team": {ndb.Key(Team, "frc254"), ndb.Key(Team, "frc604")},
        }
        cache_keys = {
            q[0] for q in get_affected_queries.districtteam_updated(affected_refs)
        }

        assert cache_keys == {
            team_query.DistrictTeamsQuery("2015fim").cache_key,
            team_query.DistrictTeamsQuery("2015mar").cache_key,
            district_query.TeamDistrictsQuery("frc254").cache_key,
            district_query.TeamDistrictsQuery("frc604").cache_key,
        }

    def test_district_updated(self) -> None:
        affected_refs = {
            "key": {ndb.Key(District, "2016ne")},
            "year": {2015, 2016},
            "abbreviation": {"ne", "chs"},
        }
        cache_keys = {
            q[0] for q in get_affected_queries.district_updated(affected_refs)
        }

        assert cache_keys == {
            district_query.DistrictsInYearQuery(2015).cache_key,
            district_query.DistrictsInYearQuery(2016).cache_key,
            district_query.DistrictHistoryQuery("ne").cache_key,
            district_query.DistrictHistoryQuery("chs").cache_key,
            district_query.DistrictQuery("2016ne").cache_key,
            district_query.DistrictAbbreviationQuery("ne").cache_key,
            district_query.DistrictAbbreviationQuery("chs").cache_key,
            district_query.TeamDistrictsQuery("frc604").cache_key,
            # Necessary because APIv3 Event models include the District model
            event_query.EventQuery("2016necmp").cache_key,
            event_query.EventListQuery(2016).cache_key,
            event_query.DistrictEventsQuery("2016ne").cache_key,
            event_query.TeamEventsQuery("frc125").cache_key,
            event_query.TeamYearEventsQuery("frc125", 2016).cache_key,
            event_query.TeamYearEventTeamsQuery("frc125", 2016).cache_key,
            event_query.EventDivisionsQuery("2016necmp").cache_key,
            event_query.RegionalEventsQuery(2016).cache_key,
            event_query.ChampionshipEventsAndDivisionsInYearQuery(2016).cache_key,
        }

    def test_renamed_district_updated(self) -> None:
        affected_refs = {
            "key": {ndb.Key(District, "2019mar")},
            "year": {2019},
            "abbreviation": {"mar"},
        }
        cache_keys = {
            q[0] for q in get_affected_queries.district_updated(affected_refs)
        }

        assert cache_keys == {
            district_query.DistrictsInYearQuery(2019).cache_key,
            district_query.DistrictHistoryQuery("mar").cache_key,
            district_query.DistrictHistoryQuery("fma").cache_key,
            district_query.DistrictQuery("2019mar").cache_key,
            district_query.DistrictQuery("2019fma").cache_key,
            district_query.DistrictAbbreviationQuery("mar").cache_key,
            district_query.DistrictAbbreviationQuery("fma").cache_key,
            event_query.DistrictEventsQuery("2019mar").cache_key,
        }

    def test_insight_updated(self) -> None:
        affected_refs = {
            "year": {0, 2023, 2024},
        }
        cache_keys = {q[0] for q in get_affected_queries.insight_updated(affected_refs)}

        assert cache_keys == {
            insight_query.InsightsLeaderboardsYearQuery(0).cache_key,
            insight_query.InsightsLeaderboardsYearQuery(2023).cache_key,
            insight_query.InsightsLeaderboardsYearQuery(2024).cache_key,
            insight_query.InsightsNotablesYearQuery(0).cache_key,
            insight_query.InsightsNotablesYearQuery(2023).cache_key,
            insight_query.InsightsNotablesYearQuery(2024).cache_key,
        }
