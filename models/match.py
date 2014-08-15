import json
import re

from google.appengine.ext import ndb

from helpers.tbavideo_helper import TBAVideoHelper
from models.event import Event
from models.team import Team


class Match(ndb.Model):
    """
    Matches represent individual matches at Events.
    Matches have many Videos.
    Matches have many Alliances.
    key_name is like 2010ct_qm10 or 2010ct_sf1m2
    """

    COMP_LEVELS = ["qm", "ef", "qf", "sf", "f"]
    ELIM_LEVELS = ["ef", "qf", "sf", "f"]
    COMP_LEVELS_VERBOSE = {
        "qm": "Quals",
        "ef": "Eighths",
        "qf": "Quarters",
        "sf": "Semis",
        "f": "Finals",
    }
    COMP_LEVELS_PLAY_ORDER = {
        'qm': 1,
        'ef': 2,
        'qf': 3,
        'sf': 4,
        'f': 5,
    }

    FRC_GAMES = [
        "frc_2012_rebr",
        "frc_2011_logo",
        "frc_2010_bkwy",
        "frc_2009_lncy",
        "frc_2008_ovdr",
        "frc_2007_rkrl",
        "frc_2006_amhi",
        "frc_2005_trpl",
        "frc_2004_frnz",
        "frc_2003_stck",
        "frc_2002_znzl",
        "frc_2001_dbdy",
        "frc_2000_coop",
        "frc_1999_trbl",
        "frc_1998_lddr",
        "frc_1997_trdt",
        "frc_1996_hxgn",
        "frc_1995_rmpr",
        "frc_1994_tpwr",
        "frc_1993_rgrg",
        "frc_1992_maiz",
        "frc_unknown",
    ]

    FRC_GAMES_BY_YEAR = {
        2012: "frc_2012_rebr",
        2011: "frc_2011_logo",
        2010: "frc_2010_bkwy",
        2009: "frc_2009_lncy",
        2008: "frc_2008_ovdr",
        2007: "frc_2007_rkrl",
        2006: "frc_2006_amhi",
        2005: "frc_2005_trpl",
        2004: "frc_2004_frnz",
        2003: "frc_2003_stck",
        2002: "frc_2002_znzl",
        2001: "frc_2001_dbdy",
        2000: "frc_2000_coop",
        1999: "frc_1999_trbl",
        1998: "frc_1998_lddr",
        1997: "frc_1997_trdt",
        1996: "frc_1996_hxgn",
        1995: "frc_1995_rmpr",
        1994: "frc_1994_tpwr",
        1993: "frc_1993_rgrg",
        1992: "frc_1992_maiz",
    }

    alliances_json = ndb.StringProperty(required=True, indexed=False)  # JSON dictionary with alliances and scores.

    # {
    # "red": {
    # "teams": ["frc177", "frc195", "frc125"], # These are Team keys
    #    "score": 25
    # },
    # "blue": {
    #    "teams": ["frc433", "frc254", "frc222"],
    #    "score": 12
    # }
    # }

    score_breakdown_json = ndb.StringProperty(indexed=False)  # JSON dictionary with score breakdowns. Fields are those used for seeding. Varies by year.
    # Example for 2014. Seeding outlined in Section 5.3.4 in the 2014 manual.
    # {"red": {
    #     "auto": 20,
    #     "assist": 40,
    #     "truss+catch": 20,
    #     "teleop_goal+foul": 20,
    # },
    # "blue"{
    #     "auto": 40,
    #     "assist": 60,
    #     "truss+catch": 10,
    #     "teleop_goal+foul": 40,
    # }}

    comp_level = ndb.StringProperty(required=True, choices=set(COMP_LEVELS))
    event = ndb.KeyProperty(kind=Event, required=True)
    game = ndb.StringProperty(required=True, choices=set(FRC_GAMES), indexed=False)
    match_number = ndb.IntegerProperty(required=True, indexed=False)
    no_auto_update = ndb.BooleanProperty(default=False, indexed=False)  # Set to True after manual update
    set_number = ndb.IntegerProperty(required=True, indexed=False)
    team_key_names = ndb.StringProperty(repeated=True)  # list of teams in Match, for indexing.
    time = ndb.DateTimeProperty()  # UTC
    time_string = ndb.StringProperty(indexed=False)  # the time as displayed on FIRST's site (event's local time)
    youtube_videos = ndb.StringProperty(repeated=True)  # list of Youtube IDs
    tba_videos = ndb.StringProperty(repeated=True)  # list of filetypes a TBA video exists for

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'event': set(),
            'team_keys': set(),
            'year': set(),
        }
        self._alliances = None
        self._score_breakdown = None
        self._tba_video = None
        self._winning_alliance = None
        self._youtube_videos = None
        super(Match, self).__init__(*args, **kw)

    @property
    def alliances(self):
        """
        Lazy load alliances_json
        """
        if self._alliances is None:
            self._alliances = json.loads(self.alliances_json)

            # score types are inconsistent in the db. convert everything to ints for now.
            for color in ['red', 'blue']:
                score = self._alliances[color]['score']
                if score is None:
                    self._alliances[color]['score'] = -1
                else:
                    self._alliances[color]['score'] = int(score)

        return self._alliances

    @property
    def score_breakdown(self):
        """
        Lazy load score_breakdown_json
        """
        if self._score_breakdown is None:
            self._score_breakdown = json.loads(self.score_breakdown_json)

        return self._score_breakdown

    @property
    def winning_alliance(self):
        if self._winning_alliance is None:
            highest_score = 0
            for alliance in self.alliances:
                if int(self.alliances[alliance]["score"]) > highest_score:
                    highest_score = int(self.alliances[alliance]["score"])
                    self._winning_alliance = alliance
                elif int(self.alliances[alliance]["score"]) == highest_score:
                    self._winning_alliance = ""
        return self._winning_alliance

    @property
    def event_key_name(self):
        return self.event.id()

    @property
    def team_keys(self):
        return [ndb.Key(Team, team_key_name) for team_key_name in self.team_key_names]

    @property
    def year(self):
        return self.event.id()[:4]

    @property
    def key_name(self):
        return self.renderKeyName(self.event_key_name, self.comp_level, self.set_number, self.match_number)

    @property
    def has_been_played(self):
        """If there are scores, it's been played"""
        for alliance in self.alliances:
            if (self.alliances[alliance]["score"] == None) or \
            (self.alliances[alliance]["score"] == -1):
                return False
        return True

    @property
    def verbose_name(self):
        if self.comp_level == "qm" or self.comp_level == "f":
            return "%s %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.match_number)
        else:
            return "%s %s Match %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.set_number, self.match_number)

    @property
    def short_name(self):
        if self.comp_level == "qm":
            return "Q%s" % self.match_number
        elif self.comp_level == "f":
            return "F%s" % self.match_number
        else:
            return "%s%s-%s" % (self.comp_level.upper(), self.set_number, self.match_number)

    @property
    def has_video(self):
        return (len(self.youtube_videos) + len(self.tba_videos)) > 0

    @property
    def details_url(self):
        return "/match/%s" % self.key_name

    @property
    def tba_video(self):
        if len(self.tba_videos) > 0:
            if self._tba_video is None:
                self._tba_video = TBAVideoHelper(self)
        return self._tba_video

    @property
    def play_order(self):
        return self.COMP_LEVELS_PLAY_ORDER[self.comp_level] * 1000000 + self.match_number * 1000 + self.set_number

    @property
    def name(self):
        return "%s" % (self.COMP_LEVELS_VERBOSE[self.comp_level])

    @property
    def youtube_videos_formatted(self):
        """
        Get youtube video ids formatted for embedding
        """
        if self._youtube_videos is None:
            self._youtube_videos = []
            for video in self.youtube_videos:
                if '#t=' in video:  # Old style-timetamp, convert it!
                    sp = video.split('#t=')
                    video_id = sp[0]
                    old_ts = sp[1]
                    match = re.match('((?P<hour>\d*?)h)?((?P<min>\d*?)m)?((?P<sec>\d*)s?)?', old_ts).groupdict()
                    hours = match['hour'] or 0
                    minutes = match['min'] or 0
                    seconds = match['sec'] or 0
                    total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds)
                    video = '%s?start=%i' % (video_id, total_seconds)
                self._youtube_videos.append(video)
        return self._youtube_videos

    @property
    def videos(self):
        videos = []
        for v in self.youtube_videos_formatted:
            videos.append({"type": "youtube", "key": v})
        if self.tba_video is not None:
            tba_path = self.tba_video.streamable_path
            if tba_path is not None:
                videos.append({"type": "tba", "key": tba_path})
        return videos

    @classmethod
    def renderKeyName(self, event_key_name, comp_level, set_number, match_number):
        if comp_level == "qm":
            return "%s_qm%s" % (event_key_name, match_number)
        else:
            return "%s_%s%sm%s" % (event_key_name, comp_level, set_number, match_number)

    @classmethod
    def validate_key_name(self, match_key):
        key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+\_(?:qm|ef|qf\dm|sf\dm|f\dm)\d+$')
        match = re.match(key_name_regex, match_key)
        return True if match else False
