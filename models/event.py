from google.appengine.ext import ndb
import datetime
import json
import logging

class Event(ndb.Model):
    """
    Events represent FIRST Robotics Competition events, both official and unofficial.
    key_name is like '2010ct'
    """
    name = ndb.StringProperty()
    event_type = ndb.StringProperty(indexed=False) # From USFIRST
    short_name = ndb.StringProperty(indexed=False) # Should not contain "Regional" or "Division", like "Hartford"
    event_short = ndb.StringProperty(required=True, indexed=False) # Smaller abbreviation like "CT"
    year = ndb.IntegerProperty(required=True)
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    venue = ndb.StringProperty(indexed=False)
    venue_address = ndb.StringProperty(indexed=False) # We can scrape this.
    location = ndb.StringProperty(indexed=False)
    official = ndb.BooleanProperty(default=False) # Is the event FIRST-official?
    first_eid = ndb.StringProperty() #from USFIRST
    facebook_eid = ndb.StringProperty(indexed=False) #from Facebook
    website = ndb.StringProperty(indexed=False)
    webcast_json = ndb.TextProperty(indexed=False) #  list of dicts, valid keys include 'type' and 'channel'
    oprs = ndb.FloatProperty(indexed=False, repeated=True)
    opr_teams = ndb.IntegerProperty(indexed=False, repeated=True)
    rankings_json = ndb.TextProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        self._awards = None
        self._matches = None
        self._rankings = None
        self._teams = None
        self._webcast = None
        super(Event, self).__init__(*args, **kw)
    
    @ndb.tasklet
    def get_awards_async(self):
        from models.award import Award
        award_keys = yield Award.query(Award.event == self.key).fetch_async(500, keys_only=True)
        self._awards = yield ndb.get_multi_async(award_keys)

    @property
    def awards(self):
        # This import is ugly, and maybe all the models should be in one file again -gregmarra 20121006
        if self._awards is None:
            self.get_awards_async().wait()
        return self._awards

    @ndb.tasklet
    def get_matches_async(self):
        from models.match import Match
        match_keys = yield Match.query(Match.event == self.key).fetch_async(500, keys_only=True)
        self._matches = yield ndb.get_multi_async(match_keys)

    @property
    def matches(self):
        # This import is ugly, and maybe all the models should be in one file again -gregmarra 20121006
        if self._matches is None:
            if self._matches is None:
                self.get_matches_async().wait()
        return self._matches

    def withinDays(self, negative_days_before, days_after):
        if not self.start_date or not self.end_date:
            return False
        today = datetime.datetime.today()
        after_start = self.start_date.date() + datetime.timedelta(days=negative_days_before) <= today.date()
        before_end = self.end_date.date() + datetime.timedelta(days=days_after) >= today.date()

        return (after_start and before_end)

    @property
    def now(self):
        return self.withinDays(0, 0)

    @property
    def within_a_day(self):
        return self.withinDays(-1, 1)

    @ndb.tasklet
    def get_teams_async(self):
        from models.event_team import EventTeam
        event_team_keys = yield EventTeam.query(EventTeam.event == self.key).fetch_async(500, keys_only=True)
        event_teams = yield ndb.get_multi_async(event_team_keys)
        team_keys = map(lambda event_team: event_team.team, event_teams)
        self._teams = yield ndb.get_multi_async(team_keys)

    @property
    def teams(self):
        if self._teams is None:
            self.get_teams_async().wait()
        return self._teams
      
    @ndb.toplevel
    def prepAwardsMatchesTeams(self):
        yield self.get_awards_async(), self.get_matches_async(), self.get_teams_async()

    @property
    def rankings(self):
        """
        Lazy load parsing rankings JSON
        """
        if self._rankings is None:
            try:
                self._rankings = json.loads(self.rankings_json)
            except Exception, e:
                self._rankings = None
        return self._rankings
    
    @property
    def webcast(self):
        """
        Lazy load parsing webcast JSON
        """
        if self._webcast is None:
            try:
                self._webcast = json.loads(self.webcast_json)
            except Exception, e:
                self._webcast = None
        return self._webcast

    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Event object before writing it.
        """
        return str(self.year) + self.event_short
    
    @property 
    def facebook_event_url(self):
        """
        Return a string of the Facebook Event URL.
        """
        return "http://www.facebook.com/event.php?eid=%s" % self.facebook_eid
    
    @property
    def details_url(self):
        """
        Returns the URL pattern for the link to this Event on TBA
        """
        return "/event/%s" % self.key_name

    @property
    def gameday_url(self):
        """
        Returns the URL pattern for the link to watch webcasts in Gameday
        """
        if self.webcast:
            gameday_link = '/gameday'
            view_num = 0
            for webcast in self.webcast:
                if view_num == 0:
                    gameday_link += '#'
                else:
                    gameday_link += '&'
                if 'type' in webcast and 'channel' in webcast:
                    gameday_link += 'view_' + str(view_num) + '=' + self.key_name + '-' + str(view_num + 1)
                view_num += 1
            return gameday_link
        else:
            return None

    # Depreciated, still here to keep GAE clean.
    webcast_url = ndb.StringProperty(indexed=False)
