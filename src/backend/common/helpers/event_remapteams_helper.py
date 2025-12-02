import json
from typing import cast, Dict, List, Optional

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.alliance import EventAlliance
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_ranking import EventRanking
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.team import Team


class EventRemapTeamsHelper:
    @classmethod
    def remap_teams(cls, event_key: EventKey) -> None:
        event: Optional[Event] = Event.get_by_id(event_key)
        if not event or not event.remap_teams:
            return None

        event.prep_awards()
        event.prep_matches()
        event.prep_teams()

        # Remap matches
        cls.remapteams_matches(event.matches, event.remap_teams)
        MatchManipulator.createOrUpdate(event.matches)

        # Remap alliance selections
        if event.alliance_selections:
            cls.remapteams_alliances(
                none_throws(event.alliance_selections), event.remap_teams
            )

        # Remap rankings
        if event.rankings:
            cls.remapteams_rankings2(event.rankings, event.remap_teams)
        EventDetailsManipulator.createOrUpdate(event.details)

        # Remap awards
        cls.remapteams_awards(event.awards, event.remap_teams)
        AwardManipulator.createOrUpdate(event.awards, auto_union=False)

    @classmethod
    def remapteams_awards(
        cls, awards: List[Award], remap_teams: Dict[str, str]
    ) -> None:
        """
        Remaps teams in awards. Mutates in place.
        In `remap_teams` dictionary, key is the old team key, value is the new team key
        """
        for award in awards:
            new_recipient_json_list = []
            new_team_list = []
            # Compute new recipient list and team list
            for recipient in award.recipient_list:
                for old_team, new_team in remap_teams.items():
                    # Convert recipient `team_number` to string for safe comparision
                    if str(recipient["team_number"]) == old_team[3:]:
                        award._dirty = True
                        recipient["team_number"] = new_team[3:]

                # Convert `team_number` down to an int, if possible
                recipient_team_number = recipient["team_number"]
                if (
                    type(recipient_team_number) is str
                    and recipient_team_number.isdigit()
                ):
                    award._dirty = True
                    recipient["team_number"] = int(recipient_team_number)

                new_recipient_json_list.append(json.dumps(recipient))
                new_team_list.append(
                    ndb.Key(Team, "frc{}".format(recipient["team_number"]))
                )

            # Update
            award.recipient_json_list = new_recipient_json_list
            award.team_list = new_team_list

    @classmethod
    def remapteams_matches(
        cls, matches: List[Match], remap_teams: Dict[str, str]
    ) -> None:
        """
        Remaps teams in matches
        Mutates in place
        """
        for match in matches:
            for old_team, new_team in remap_teams.items():
                # Update alliances
                for color in ALLIANCE_COLORS:
                    for attr in ["teams", "surrogates", "dqs"]:
                        team_keys = cast(
                            List[TeamKey], match.alliances[color].get(attr, [])
                        )
                        for i, key in enumerate(team_keys):
                            if key == old_team:
                                match._dirty = True
                                match.alliances[color][attr][  # pyre-ignore[26]
                                    i
                                ] = new_team
                                match.alliances_json = json.dumps(match.alliances)

                # Update team key names
                match.team_key_names = []
                for alliance in match.alliances:
                    match.team_key_names.extend(
                        none_throws(match.alliances[alliance].get("teams", None))
                    )

    @classmethod
    def remapteams_alliances(
        cls, alliance_selections: List[EventAlliance], remap_teams: Dict[str, str]
    ) -> None:
        """
        Remaps teams in alliance selections
        Mutates in place
        """
        for row in alliance_selections:
            for choice in ["picks", "declines"]:
                for old_team, new_team in remap_teams.items():
                    team_keys = cast(List[TeamKey], row.get(choice, []))
                    for i, key in enumerate(team_keys):
                        if key == old_team:
                            row[choice][i] = new_team  # pyre-ignore[26,6]

    @classmethod
    def remapteams_rankings2(
        cls, rankings2: List[EventRanking], remap_teams: Dict[str, str]
    ) -> None:
        """
        Remaps teams in rankings2
        Mutates in place
        """
        for ranking in rankings2:
            if ranking["team_key"] in remap_teams:
                ranking["team_key"] = remap_teams[ranking["team_key"]]
