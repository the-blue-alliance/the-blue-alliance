from google.appengine.ext import ndb
import datetime
import json
import re
from consts.event_type import EventType


class Event(ndb.Model):
    """
    Events represent FIRST Robotics Competition events, both official and unofficial.
    key_name is like '2010ct'
    """
    name = ndb.StringProperty()
    event_type_enum = ndb.IntegerProperty(required=True)
    short_name = ndb.StringProperty(indexed=False)  # Should not contain "Regional" or "Division", like "Hartford"
    event_short = ndb.StringProperty(required=True, indexed=False)  # Smaller abbreviation like "CT"
    year = ndb.IntegerProperty(required=True)
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    venue = ndb.StringProperty(indexed=False)
    venue_address = ndb.StringProperty(indexed=False)  # We can scrape this.
    location = ndb.StringProperty(indexed=False)  # in the format "locality, region, country". similar to Team.address
    timezone_id = ndb.StringProperty()  # such as 'America/Los_Angeles' or 'Asia/Jerusalem'
    official = ndb.BooleanProperty(default=False)  # Is the event FIRST-official?
    first_eid = ndb.StringProperty()  # from USFIRST
    facebook_eid = ndb.StringProperty(indexed=False)  # from Facebook
    website = ndb.StringProperty(indexed=False)
    webcast_json = ndb.TextProperty(indexed=False)  # list of dicts, valid keys include 'type' and 'channel'
    matchstats_json = ndb.TextProperty(indexed=False)  # for OPR, DPR, CCWM, etc.
    rankings_json = ndb.TextProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        self._awards = None
        self._matches = None
        self._matchstats = None
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
        from models.award import Award
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
        from models.match import Match
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

    @property
    def past(self):
        return self.end_date.date() < datetime.date.today() and not self.within_a_day

    @property
    def future(self):
        return self.start_date.date() > datetime.date.today() and not self.within_a_day

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

    @ndb.toplevel
    def prepTeams(self):
        yield self.get_teams_async()

    @ndb.toplevel
    def prepTeamsMatches(self):
        yield self.get_matches_async(), self.get_teams_async()

    @property
    def matchstats(self):
        """
        Lazy load parsing matchstats JSON
        """
        if self._matchstats is None:
            try:
                self._matchstats = json.loads(self.matchstats_json)
            except Exception, e:
                self._matchstats = None
        return self._matchstats

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

    @classmethod
    def validate_key_name(self, event_key):
        key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+[1-9]?$')
        match = re.match(key_name_regex, event_key)
        return True if match else False

    @property
    def event_type_str(self):
        return EventType.type_names[self.event_type_enum]
