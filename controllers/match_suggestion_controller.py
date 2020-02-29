import json
from collections import defaultdict

from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper


class MatchSuggestionHandler(LoggedInHandler):

    def get_qual_bluezone_score(self, prediction):
        redScore = prediction['red']['score']
        blueScore = prediction['blue']['score']
        winningScore = redScore if redScore > blueScore else blueScore
        losingScore = redScore if redScore < blueScore else blueScore
        scorePower = min(float(winningScore + 2 * losingScore) / (200.0 * 3) * 50, 50)  # High score ~200, up to 50 BlueZone points
        skillPower = min((
            min(prediction['red']['power_cells_scored'] / 49, 1) +
            min(prediction['blue']['power_cells_scored'] / 49, 1) +
            min(prediction['red']['endgame_points'] / 65, 1) +
            min(prediction['blue']['endgame_points'] / 65, 1)
        ) * 50 / 4, 50)  # Up to 50 BlueZone points

        return scorePower + skillPower

    def get_elim_bluezone_score(self, prediction):
        return self.get_qual_bluezone_score(prediction)
        # return min(100, (
        #     min(prediction['red']['auto_points'] * prediction['red']['auto_points'], 2000) / 2000 +
        #     min(prediction['blue']['auto_points'] * prediction['blue']['auto_points'], 2000) / 2000 +
        #     min(prediction['red']['endgame_points'] * prediction['red']['endgame_points'], 8100) / 8100 +
        #     min(prediction['blue']['endgame_points'] * prediction['blue']['endgame_points'], 8100) / 8100
        # ) * 25)

    def get(self):
        self._require_registration()

        current_events = filter(lambda e: e.now, EventHelper.getEventsWithinADay())
        popular_teams_events = TeamHelper.getPopularTeamsEvents(current_events)

        popular_team_keys = set()
        for team, _ in popular_teams_events:
            popular_team_keys.add(team.key.id())

        for event in current_events:
            event.prep_details()
            event.prep_matches()

        finished_matches = []
        current_matches = []
        upcoming_matches = []
        ranks = {}
        alliances = {}
        for event in current_events:
            if not event.details:
                continue
            finished_matches += MatchHelper.recentMatches(event.matches, num=1)
            for i, match in enumerate(MatchHelper.upcomingMatches(event.matches, num=3)):
                if not match.time:
                    continue

                if not event.details.predictions or match.key.id() not in event.details.predictions['match_predictions']['qual' if match.comp_level == 'qm' else 'playoff']:
                    match.prediction = defaultdict(lambda: defaultdict(float))
                    match.bluezone_score = 0
                else:
                    match.prediction = event.details.predictions['match_predictions']['qual' if match.comp_level == 'qm' else 'playoff'][match.key.id()]
                    match.bluezone_score = self.get_qual_bluezone_score(match.prediction) if match.comp_level == 'qm' else self.get_elim_bluezone_score(match.prediction)
                if i == 0:
                    current_matches.append(match)
                else:
                    upcoming_matches.append(match)
            if event.details.rankings2:
                for rank in event.details.rankings2:
                    ranks[rank['team_key']] = rank['rank']
            if event.alliance_selections:
                for i, alliance in enumerate(event.alliance_selections):
                    for pick in alliance['picks']:
                        alliances[pick] = i + 1

        finished_matches = sorted(finished_matches, key=lambda m: m.actual_time if m.actual_time else m.time)
        current_matches = sorted(current_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)
        upcoming_matches = sorted(upcoming_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)

        self.template_values.update({
            'finished_matches': finished_matches,
            'current_matches': current_matches,
            'upcoming_matches': upcoming_matches,
            'ranks': ranks,
            'alliances': alliances,
            'popular_team_keys': popular_team_keys,
        })

        self.response.out.write(jinja2_engine.render('match_suggestion.html', self.template_values))
