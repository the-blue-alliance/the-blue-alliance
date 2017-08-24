from base_controller import CacheableHandler


class ShortTeamHandler(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "short_team_canonical_{}"  # (team_number)

    def get(self, team_number):
        return self.redirect("/team/%s" % int(team_number))

class ShortEventHandler(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "short_event_detail_{}"  # (event_key)

    def get(self, event_key):
        return self.redirect("/event/%s" % event_key)
