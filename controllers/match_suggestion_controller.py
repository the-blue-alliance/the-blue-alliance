import json
from collections import defaultdict

from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper


class MatchSuggestionHandler(LoggedInHandler):

    def get_qual_bluezone_score(self, prediction):
        return min(100, (
            min(prediction['red']['auto_points'] * prediction['red']['auto_points'], 3600) / 1200 +
            min(prediction['blue']['auto_points'] * prediction['blue']['auto_points'], 3600) / 1200 +
            min(prediction['red']['endgame_points'] * prediction['red']['endgame_points'], 144) / 64 +
            min(prediction['blue']['endgame_points'] * prediction['blue']['endgame_points'], 144) / 64
        ) * 25)

    def get_elim_bluezone_score(self, prediction):
        return min(100, (
            min(prediction['red']['auto_points'] * prediction['red']['auto_points'], 8000) / 3000 +
            min(prediction['blue']['auto_points'] * prediction['blue']['auto_points'], 8000) / 3000 +
            min(prediction['red']['endgame_points'] * prediction['red']['endgame_points'], 144) / 72 +
            min(prediction['blue']['endgame_points'] * prediction['blue']['endgame_points'], 144) / 72
        ) * 25)

    def get(self):
        self._require_registration()

        current_events = filter(lambda e: e.now, EventHelper.getEventsWithinADay())

        for event in current_events:
            event.prep_details()
            event.prep_matches()

        finished_matches = []
        current_matches = []
        upcoming_matches = []
        ranks = {}
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
        finished_matches = sorted(finished_matches, key=lambda m: m.actual_time if m.actual_time else m.time)
        current_matches = sorted(current_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)
        upcoming_matches = sorted(upcoming_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)

        self.template_values.update({
            'finished_matches': finished_matches,
            'current_matches': current_matches,
            'upcoming_matches': upcoming_matches,
            'ranks': ranks,
        })

        self.response.out.write(jinja2_engine.render('match_suggestion.html', self.template_values))
