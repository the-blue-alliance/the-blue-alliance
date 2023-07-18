import datetime
from typing import List, Set, Tuple

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.match_helper import MatchHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamId, TeamKey
from backend.common.models.match import Match
from backend.common.models.team import Team


class EventTeamUpdater:
    @classmethod
    def update(
        self, event_key: EventKey, allow_deletes: bool = False
    ) -> Tuple[List[Team], List[EventTeam], Set[ndb.Key]]:
        """
        Updates EventTeams for an event.
        Returns a tuple of (teams, event_teams, event_team_keys_to_delete)
        An EventTeam is valid iff the team:
        a) played a match at the event,
        b) the team received an award at the event,
        c) the event has not yet occurred,
        d) the team is on an alliance
        e) the winning alliance of one of this event's divisions
        f) or the event is not from the current year. (This is to make sure we don't delete old data we may no longer be able to scrape)
        """
        event = none_throws(Event.get_by_id(event_key))
        cur_year = datetime.datetime.now().year

        # Add teams from Matches and Awards
        team_ids: Set[TeamId] = set()
        match_key_futures = Match.query(Match.event == event.key).fetch_async(
            1000, keys_only=True
        )
        award_key_futures = Award.query(Award.event == event.key).fetch_async(
            1000, keys_only=True
        )
        match_futures = ndb.get_multi_async(match_key_futures.get_result())
        award_futures = ndb.get_multi_async(award_key_futures.get_result())

        division_futures = (
            ndb.get_multi_async(event.divisions) if event.divisions else []
        )
        division_matches_futures = [
            Match.query(Match.event == division).fetch_async(1000)
            for division in (event.divisions or [])
        ]

        for match_future in match_futures:
            match = match_future.get_result()
            for team in match.team_key_names:
                team_ids.add(team)
        for award_future in award_futures:
            award = award_future.get_result()
            for team_key in award.team_list:
                team_ids.add(team_key.id())

        # Add teams from Alliances
        for team in event.alliance_teams:
            team_ids.add(team)

        # Add teams from division winners
        if event.divisions:
            for division_future, matches_future in zip(
                division_futures, division_matches_futures
            ):
                division_winners = self.get_event_winners(
                    division_future.get_result(), matches_future.get_result()
                )
                team_ids = team_ids.union(division_winners)

        # Create or update EventTeams
        teams = [
            Team(id=team_id, team_number=int(team_id[3:]))
            for team_id in team_ids
            if team_id[3:].isdigit()
        ]

        if teams:
            event_teams = [
                EventTeam(
                    id=event_key + "_" + team.key_name,
                    event=event.key,
                    team=team.key,
                    year=event.year,
                )
                for team in teams
            ]
        else:
            event_teams = []

        # Delete EventTeams for teams who did not participate in the event
        # Only runs if event is over
        existing_event_teams_keys = EventTeam.query(EventTeam.event == event.key).fetch(
            1000, keys_only=True
        )
        existing_event_teams = ndb.get_multi(existing_event_teams_keys)
        existing_team_ids: Set[TeamId] = set()
        for et in existing_event_teams:
            existing_team_ids.add(et.team.id())

        et_keys_to_delete: Set[ndb.Key] = set()
        if allow_deletes or (event.year == cur_year and event.past):
            for team_id in existing_team_ids.difference(
                [team.key.id() for team in teams]
            ):
                et_key_name = "{}_{}".format(event.key_name, team_id)
                et_keys_to_delete.add(ndb.Key(EventTeam, et_key_name))

        return teams, event_teams, et_keys_to_delete

    @classmethod
    def get_event_winners(cls, event: Event, matches: List[Match]) -> Set[TeamKey]:
        """
        First alliance to win two finals matches is the winner
        """
        _, matches_by_type = MatchHelper.organized_matches(matches)
        if CompLevel.F not in matches_by_type or not matches_by_type[CompLevel.F]:
            return set()

        finals_matches: List[Match] = matches_by_type[CompLevel.F]
        red_wins = 0
        blue_wins = 0

        red_teams = set()
        blue_teams = set()
        for match in finals_matches:
            if match.has_been_played:
                red_teams = red_teams.union(match.alliances[AllianceColor.RED]["teams"])
                blue_teams = blue_teams.union(
                    match.alliances[AllianceColor.BLUE]["teams"]
                )

                if match.winning_alliance == AllianceColor.RED:
                    red_wins += 1
                elif match.winning_alliance == AllianceColor.BLUE:
                    blue_wins += 1

        winning_teams = set()
        if red_wins >= 2:
            winning_teams = red_teams
        elif blue_wins >= 2:
            winning_teams = blue_teams

        # Return the entire alliance
        alliance_selections = event.alliance_selections
        if alliance_selections:
            for alliance in alliance_selections:
                if len(winning_teams.intersection(set(alliance["picks"]))) >= 2:
                    complete_alliance = set(alliance["picks"]) if alliance else set()
                    if alliance and alliance.get("backup"):
                        complete_alliance.add(alliance["backup"]["in"])
                    return complete_alliance

        # Fall back to the match winners
        return winning_teams
