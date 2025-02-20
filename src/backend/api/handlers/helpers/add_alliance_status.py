from typing import List

from google.appengine.ext import ndb

from backend.common.models.alliance import EventAlliance
from backend.common.models.event_team import EventTeam


# Adds the alliance captain's EventTeamStatusPlayoff to the alliance status.
def add_alliance_status(
    event_key: str, alliances: List[EventAlliance]
) -> List[EventAlliance]:
    captain_team_keys = []
    for alliance in alliances:
        if alliance["picks"]:
            captain_team_keys.append(alliance["picks"][0])

    event_team_keys = [
        ndb.Key(EventTeam, "{}_{}".format(event_key, team_key))
        for team_key in captain_team_keys
    ]
    captain_eventteams_future = ndb.get_multi_async(event_team_keys)
    with_status = []
    for captain_future, alliance in zip(captain_eventteams_future, alliances):
        captain = captain_future.get_result()
        if (
            captain
            and captain.status
            and captain.status.get("alliance")
            and captain.status.get("playoff")
        ):
            alliance["status"] = captain.status.get("playoff")

        with_status.append(alliance)

    return with_status
