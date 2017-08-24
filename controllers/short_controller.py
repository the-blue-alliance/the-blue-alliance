from base_controller import CacheableHandler


class ShortTeamHandler(CacheableHandler):
    def get(self, team_number):
        return self.redirect("/team/%s" % int(team_number))

class ShortEventHandler(CacheableHandler):
    def get(self, event_key):
        return self.redirect("/event/%s" % event_key)
