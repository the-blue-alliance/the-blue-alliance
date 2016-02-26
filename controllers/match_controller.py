import os

from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from models.event import Event
from models.match import Match


class MatchDetail(CacheableHandler):
    """
    Display a Match.
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "match_detail_{}"  # (match_key)

    defense_render_names = {
        'A_ChevalDeFrise': 'Cheval De Frise',
        'A_Portcullis': 'Portcullis',
        'B_Ramparts': 'Ramparts',
        'B_Moat': 'Moat',
        'C_SallyPort': 'Sally Port',
        'C_Drawbridge': 'Drawbridge',
        'D_RoughTerrain': 'Rough Terrain',
        'D_RockWall': 'Rock Wall'
    }

    def __init__(self, *args, **kw):
        super(MatchDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, match_key):
        if not match_key:
            return self.redirect("/")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(match_key)
        super(MatchDetail, self).get(match_key)

    def _render(self, match_key):
        try:
            match_future = Match.get_by_id_async(match_key)
            event_future = Event.get_by_id_async(match_key.split("_")[0])
            match = match_future.get_result()
            event = event_future.get_result()
        except Exception, e:
            self.abort(404)

        if not match:
            self.abort(404)

        match_breakdown_template = None
        if match.score_breakdown is not None:
            match_breakdown_template = 'match_partials/match_breakdown_{}.html'.format(match.year)

            # Specifc to 2016 Game
            self.add_defense_render_names(match.score_breakdown['red'])
            self.add_defense_render_names(match.score_breakdown['blue'])

        self.template_values.update({
            "event": event,
            "match": match,
            "match_breakdown_template": match_breakdown_template,
        })

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/match_details.html')
        return template.render(path, self.template_values)

    """
    Adds new properties to the score breadown dict because they don't come formatted pretty
    """
    @classmethod
    def add_defense_render_names(self, alliance_breadown):
        for i in range(2, 6):
            key = "position{}".format(i)
            alliance_breadown[key] = self.defense_render_names[alliance_breadown[key]]
