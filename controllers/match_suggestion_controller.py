import json

from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper


class MatchSuggestionHandler(LoggedInHandler):
    def get(self):
        self._require_registration()

        current_events = filter(lambda e: e.now, EventHelper.getEventsWithinADay())

        for event in current_events:
            event.prep_details()
            event.prep_matches()

        current_matches = []
        upcoming_matches = []
        ranks = {}
        for event in current_events:
            for i, match in enumerate(MatchHelper.upcomingMatches(event.matches, num=3)):
                match.prediction = event.details.predictions['match_predictions']['qual' if match.comp_level == 'qm' else 'playoff'][match.key.id()]
                if i == 0:
                    current_matches.append(match)
                else:
                    upcoming_matches.append(match)
            for rank in event.details.rankings2:
                ranks[rank['team_key']] = rank['rank']
        current_matches = sorted(current_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)
        upcoming_matches = sorted(upcoming_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time)

        self.template_values.update({
            'current_matches': current_matches,
            'upcoming_matches': upcoming_matches,
            'ranks': ranks,
        })

        self.response.out.write(jinja2_engine.render('match_suggestion.html', self.template_values))
