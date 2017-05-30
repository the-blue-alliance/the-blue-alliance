import json
from collections import defaultdict

from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper


class MatchSuggestionHandler(LoggedInHandler):

    def get_qual_bluezone_score(self, prediction):
        return min(100, (
            min(prediction['red']['pressure'] * prediction['red']['pressure'], 3600) / 1200 +
            min(prediction['blue']['pressure'] * prediction['blue']['pressure'], 3600) / 1200 +
            min(prediction['red']['gears'] * prediction['red']['gears'], 144) / 64 +
            min(prediction['blue']['gears'] * prediction['blue']['gears'], 144) / 64
        ) * 25)

    def get_elim_bluezone_score(self, prediction):
        return min(100, (
            min(prediction['red']['pressure'] * prediction['red']['pressure'], 8000) / 3000 +
            min(prediction['blue']['pressure'] * prediction['blue']['pressure'], 8000) / 3000 +
            min(prediction['red']['gears'] * prediction['red']['gears'], 144) / 72 +
            min(prediction['blue']['gears'] * prediction['blue']['gears'], 144) / 72
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
            finished_matches += MatchHelper.recentMatches(event.matches, num=1)
            for i, match in enumerate(MatchHelper.upcomingMatches(event.matches, num=3)):
                if match.key.id() not in event.details.predictions['match_predictions']['qual' if match.comp_level == 'qm' else 'playoff']:
                    match.prediction = defaultdict(lambda: defaultdict())
                    match.bluezone_score = 0
                    continue
                match.prediction = event.details.predictions['match_predictions']['qual' if match.comp_level == 'qm' else 'playoff'][match.key.id()]
                match.bluezone_score = self.get_qual_bluezone_score(match.prediction) if match.comp_level == 'qm' else self.get_elim_bluezone_score(match.prediction)
                if i == 0:
                    current_matches.append(match)
                else:
                    upcoming_matches.append(match)
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
