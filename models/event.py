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

    def __init__(self, *args, **kw):
        self._awards = None
        self._awards_future = None
        self._matches = None
        self._matches_future = None
        self._rankings = None
        self._teams_future = None
        self._teams = None
        self._webcast = None
        super(Event, self).__init__(*args, **kw)
    
    def prepAwards(self):
        from models.award import Award
        if self._awards_future is None:
            self._awards_future = Award.query(Award.event == self.key).fetch_async(500)

    @property
    def awards(self):
        # This import is ugly, and maybe all the models should be in one file again -gregmarra 20121006
        from models.award import Award
        if self._awards is None:
            self.prepAwards()
            self._awards = self._awards_future.get_result()
        return self._awards

    def prepMatches(self):
        from models.match import Match
        if self._matches_future is None:
            self._matches_future = Match.query(Match.event == self.key).fetch_async(500)

    @property
    def matches(self):
        # This import is ugly, and maybe all the models should be in one file again -gregmarra 20121006
        from models.match import Match
        if self._matches is None:
            self.prepMatches()
            self._matches = self._matches_future.get_result()
        return self._matches

    @property
    def now(self):
        if datetime.datetime.today().date() >= self.start_date.date()and datetime.datetime.today().date() <= self.end_date.date():
            return True
        else:
            return False

    def prepTeams(self):
        # TODO there is a way to do this with yields such that this would be a
        # generator function that would yield, and if two sets of ndb fetches
        # went by would cleanly do itself without forcing a fetch.
        # -gregmarra 20121007
        from models.event_team import EventTeam
        if self._teams_future is None:
            self._event_teams_future = EventTeam.query(EventTeam.event == self.key).fetch_async(500)

    @property
    def teams(self):
        # This import is ugly, and maybe all the models should be in one file again -gregmarra 20121006
        from models.event_team import EventTeam
        if self._teams is None:
            team_keys = [event_team.team for event_team in self._event_teams_future.get_result()]
            teams = ndb.get_multi(team_keys)
            self._teams = sorted(teams, key = lambda team: team.team_number) 
        return self._teams

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

    # Depreciated, still here to keep GAE clean.
    webcast_url = ndb.StringProperty(indexed=False)
