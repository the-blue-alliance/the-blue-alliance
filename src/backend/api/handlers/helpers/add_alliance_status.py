from google.cloud import ndb

from backend.common.models.event_team import EventTeam


def add_alliance_status(event_key, alliances):
    captain_team_keys = []
    for alliance in alliances:
        if alliance["picks"]:
            captain_team_keys.append(alliance["picks"][0])

    event_team_keys = [
        ndb.Key(EventTeam, "{}_{}".format(event_key, team_key))
        for team_key in captain_team_keys
    ]
    captain_eventteams_future = ndb.get_multi_async(event_team_keys)
    for captain_future, alliance in zip(captain_eventteams_future, alliances):
        captain = captain_future.get_result()
        if (
            captain
            and captain.status
            and "alliance" in captain.status
            and "playoff" in captain.status
        ):
            alliance["status"] = captain.status["playoff"]
        else:
            alliance["status"] = "unknown"
    return alliances
