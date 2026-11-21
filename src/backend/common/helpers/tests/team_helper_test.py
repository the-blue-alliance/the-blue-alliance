from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.helpers.team_helper import TeamHelper
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.favorite import Favorite
from backend.common.models.team import Team


def test_sort_teams() -> None:
    t1 = Team(id="frc1", team_number=1)
    t254 = Team(id="frc254", team_number=254)
    assert TeamHelper.sort_teams([t254, None, t1]) == [t1, t254]


def test_get_popular_teams_events(ndb_stub, memcache_stub) -> None:
    events = []
    for event_key, team_keys in [
        ("2020nyny", ["frc254", "frc1124"]),
        ("2020ctha", ["frc177"]),
    ]:
        event = Event(
            id=event_key,
            year=2020,
            event_short=event_key[4:],
            event_type_enum=EventType.REGIONAL,
        )
        event.put()
        events.append(event)
        for team_key in team_keys:
            Team(id=team_key, team_number=int(team_key[3:])).put()
            EventTeam(
                id=f"{event_key}_{team_key}",
                event=event.key,
                team=ndb.Key(Team, team_key),
                year=2020,
            ).put()

    for user_id, team_key in [("u1", "frc254"), ("u2", "frc254"), ("u1", "frc177")]:
        Favorite(
            parent=ndb.Key("Account", user_id),
            user_id=user_id,
            model_key=team_key,
            model_type=ModelType.TEAM,
        ).put()

    expected = [
        (Team.get_by_id("frc177"), events[1]),
        (Team.get_by_id("frc254"), events[0]),
        (Team.get_by_id("frc1124"), events[0]),
    ]
    assert TeamHelper.getPopularTeamsEvents(events) == expected

    # A second call is served from memcache
    assert TeamHelper.getPopularTeamsEvents(events) == expected
