from google.appengine.ext import ndb
import datetime
import json
import pytz
import re

from consts.district_type import DistrictType
from consts.event_type import EventType
from consts.ranking_indexes import RankingIndexes


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
    event_district_enum = ndb.IntegerProperty(default=DistrictType.NO_DISTRICT)
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    venue = ndb.StringProperty(indexed=False)  # Name of the event venue
    venue_address = ndb.StringProperty(indexed=False)  # Most detailed venue address (includes venue, street, and location separated by \n)
    city = ndb.StringProperty()  # Equivalent to locality. From FRCAPI
    state_prov = ndb.StringProperty()  # Equivalent to region. From FRCAPI
    country = ndb.StringProperty()  # From FRCAPI
    timezone_id = ndb.StringProperty()  # such as 'America/Los_Angeles' or 'Asia/Jerusalem'
    official = ndb.BooleanProperty(default=False)  # Is the event FIRST-official?
    first_eid = ndb.StringProperty()  # from USFIRST
    facebook_eid = ndb.StringProperty(indexed=False)  # from Facebook
    custom_hashtag = ndb.StringProperty(indexed=False)  # Custom HashTag
    website = ndb.StringProperty(indexed=False)
    webcast_json = ndb.TextProperty(indexed=False)  # list of dicts, valid keys include 'type' and 'channel'
    matchstats_json = ndb.TextProperty(indexed=False)  # for OPR, DPR, CCWM, etc.
    rankings_json = ndb.TextProperty(indexed=False)
    alliance_selections_json = ndb.TextProperty(indexed=False)  # Formatted as: [{'picks': [captain, pick1, pick2, 'frc123', ...], 'declines':[decline1, decline2, ...] }, {'picks': [], 'declines': []}, ... ]
    district_points_json = ndb.TextProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'key': set(),
            'year': set(),
            'event_district_abbrev': set(),
            'event_district_key': set()
        }
        self._alliance_selections = None
        self._awards = None
        self._district_points = None
        self._matches = None
        self._matchstats = None
        self._rankings = None
        self._teams = None
        self._venue_address_safe = None
        self._webcast = None
        self._updated_attrs = []  # Used in EventManipulator to track what changed
        self._rankings_enhanced = None
        super(Event, self).__init__(*args, **kw)

    @ndb.tasklet
    def get_awards_async(self):
        from database import award_query
        self._awards = yield award_query.EventAwardsQuery(self.key_name).fetch_async()

    @property
    def alliance_selections(self):
        """
        Lazy load alliance_selections JSON
        """
        if self._alliance_selections is None:
            try:
                self._alliance_selections = json.loads(self.alliance_selections_json)
            except Exception, e:
                self._alliance_selections = None
        return self._alliance_selections

    @property
    def alliance_teams(self):
        """
        Load a list of team keys playing in elims
        """
        alliances = self.alliance_selections
        if alliances is None:
            return []
        teams = []
        for alliance in alliances:
            for pick in alliance['picks']:
                teams.append(pick)
        return teams

    @property
    def awards(self):
        if self._awards is None:
            self.get_awards_async().wait()
        return self._awards

    @property
    def district_points(self):
        """
        Lazy load district_points JSON
        """
        if self._district_points is None:
            try:
                self._district_points = json.loads(self.district_points_json)
            except Exception, e:
                self._district_points = None
        return self._district_points

    @ndb.tasklet
    def get_matches_async(self):
        from database import match_query
        self._matches = yield match_query.EventMatchesQuery(self.key_name).fetch_async()

    @property
    def matches(self):
        if self._matches is None:
            if self._matches is None:
                self.get_matches_async().wait()
        return self._matches

    def local_time(self):
        now = datetime.datetime.now()
        if self.timezone_id is not None:
            tz = pytz.timezone(self.timezone_id)
            try:
                now = now + tz.utcoffset(now)
            except pytz.NonExistentTimeError:  # may happen during DST
                now = now + tz.utcoffset(now + datetime.timedelta(hours=1))  # add offset to get out of non-existant time
        return now

    def withinDays(self, negative_days_before, days_after):
        if not self.start_date or not self.end_date:
            return False
        now = self.local_time()
        after_start = self.start_date.date() + datetime.timedelta(days=negative_days_before) <= now.date()
        before_end = self.end_date.date() + datetime.timedelta(days=days_after) >= now.date()

        return (after_start and before_end)

    @property
    def now(self):
        if self.timezone_id is not None:
            return self.withinDays(0, 0)
        else:
            return self.within_a_day  # overestimate what is "now" if no timezone

    @property
    def within_a_day(self):
        return self.withinDays(-1, 1)

    @property
    def past(self):
        return self.end_date.date() < datetime.date.today() and not self.within_a_day

    @property
    def future(self):
        return self.start_date.date() > datetime.date.today() and not self.within_a_day

    @property
    def starts_today(self):
        return self.start_date.date() == self.local_time().date()

    @property
    def ends_today(self):
        return self.end_date.date() == self.local_time().date()

    @ndb.tasklet
    def get_teams_async(self):
        from database import team_query
        self._teams = yield team_query.EventTeamsQuery(self.key_name).fetch_async()

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
                self._rankings = [[str(el) for el in row] for row in json.loads(self.rankings_json)]
            except Exception, e:
                self._rankings = None
        return self._rankings

    @property
    def rankings_enhanced(self):
        valid_years = RankingIndexes.CUMULATIVE_RANKING_YEARS
        rankings = self.rankings
        if rankings is not None and self.year in valid_years and self.official:
            self._rankings_enhanced = { "ranking_score_per_match": {},
                                        "match_offset": None, }
            team_index = RankingIndexes.TEAM_NUMBER
            rp_index = RankingIndexes.CUMULATIVE_RANKING_SCORE[self.year]
            matches_played_index = RankingIndexes.MATCHES_PLAYED[self.year]

            max_matches = 0
            if self.within_a_day:
                max_matches = max([int(el[matches_played_index]) for el in rankings[1:]])
                self._rankings_enhanced["match_offset"] = {}

            for ranking in rankings[1:]:
                team_number = ranking[team_index]
                ranking_score = float(ranking[rp_index])
                matches_played = int(ranking[matches_played_index])
                if matches_played == 0:
                    ranking_score_per_match = 0
                else:
                    ranking_score_per_match = round(ranking_score / matches_played, 2)
                self._rankings_enhanced["ranking_score_per_match"][team_number] = ranking_score_per_match
                if self.within_a_day:
                    self._rankings_enhanced["match_offset"][team_number] = matches_played - max_matches
        else:
            self._rankings_enhanced = None
        return self._rankings_enhanced

    @property
    def location(self):
        split_location = []
        if self.city:
            split_location.append(self.city)
        if self.state_prov:
            split_location.append(self.state_prov)
        if self.country:
            split_location.append(self.country)
        return ', '.join(split_location)

    @property
    def venue_or_venue_from_address(self):
        if self.venue:
            return self.venue
        else:
            try:
                return self.venue_address.split('\r\n')[0]
            except:
                return None

    @property
    def venue_address_safe(self):
        """
        Construct (not detailed) venue address if detailed venue address doesn't exist
        """
        if not self.venue_address:
            if not self.venue or not self.location:
                self._venue_address_safe = None
            else:
                self._venue_address_safe = "{}\n{}".format(self.venue.encode('utf-8'), self.location.encode('utf-8'))
        else:
            self._venue_address_safe = self.venue_address.replace('\r\n', '\n')
        return self._venue_address_safe

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

    @property
    def hashtag(self):
        """
        Return the hashtag used for the event.
        """
        if self.custom_hashtag:
            return self.custom_hashtag
        else:
            return "frc" + self.event_short

    # Depreciated, still here to keep GAE clean.
    webcast_url = ndb.StringProperty(indexed=False)

    @classmethod
    def validate_key_name(self, event_key):
        key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+[0-9]?$')
        match = re.match(key_name_regex, event_key)
        return True if match else False

    @property
    def event_district_str(self):
        return DistrictType.type_names.get(self.event_district_enum, None)

    @property
    def event_district_abbrev(self):
        return DistrictType.type_abbrevs.get(self.event_district_enum, None)

    @property
    def event_district_key(self):
        district_abbrev = DistrictType.type_abbrevs.get(self.event_district_enum, None)
        if district_abbrev is None:
            return None
        else:
            return '{}{}'.format(self.year, district_abbrev)

    @property
    def event_type_str(self):
        return EventType.type_names[self.event_type_enum]

    @property
    def display_name(self):
        return self.name if self.short_name is None else self.short_name
