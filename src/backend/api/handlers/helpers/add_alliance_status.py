from backend.common.models.alliance import EventAlliance
from backend.common.models.keys import EventKey
from backend.common.queries.team_query import EventEventTeamsQuery


# Adds the alliance captain's EventTeamStatusPlayoff to the alliance status.
def add_alliance_status(
    event_key: str, alliances: list[EventAlliance]
) -> list[EventAlliance]:
    event_teams = EventEventTeamsQuery(event_key=EventKey(event_key)).fetch()
    event_teams_by_key = {
        event_team.team.id(): event_team
        for event_team in event_teams
        if event_team.team is not None
    }
    with_status = []
    for alliance in alliances:
        if alliance.get("picks"):
            captain_team_key = alliance["picks"][0]
            captain = event_teams_by_key.get(captain_team_key)
            if (
                captain
                and captain.status
                and captain.status.get("alliance")
                and captain.status.get("playoff")
            ):
                playoff_status = captain.status.get("playoff")
                if playoff_status is not None:
                    alliance["status"] = playoff_status

        with_status.append(alliance)

    return with_status
