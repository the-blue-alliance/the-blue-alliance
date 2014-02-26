import json
import re

from google.appengine.ext import ndb

from helpers.tbavideo_helper import TBAVideoHelper
from models.event import Event


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

    comp_level = ndb.StringProperty(required=True, choices=set(COMP_LEVELS))
    event = ndb.KeyProperty(kind=Event, required=True)
    game = ndb.StringProperty(required=True, choices=set(FRC_GAMES), indexed=False)
    match_number = ndb.IntegerProperty(required=True, indexed=False)
    no_auto_update = ndb.BooleanProperty(default=False, indexed=False)  # Set to True after manual update
    set_number = ndb.IntegerProperty(required=True, indexed=False)
    team_key_names = ndb.StringProperty(repeated=True)  # list of teams in Match, for indexing.
    time = ndb.DateTimeProperty(indexed=False)
    time_string = ndb.StringProperty(indexed=False)  # the time as displayed on FIRST's site
    youtube_videos = ndb.StringProperty(repeated=True)  # list of Youtube IDs
    tba_videos = ndb.StringProperty(repeated=True)  # list of filetypes a TBA video exists for

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._alliances = None
        self._tba_video = None
        self._winning_alliance = None
        super(Match, self).__init__(*args, **kw)

    @property
    def alliances(self):
        """
        Lazy load alliances_json
        """
        if self._alliances is None:
            self._alliances = json.loads(self.alliances_json)
        return self._alliances

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

    def clearAlliances(self):
        self._alliances = None
