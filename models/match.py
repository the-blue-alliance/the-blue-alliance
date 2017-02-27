import json
import numpy as np
import re

from google.appengine.ext import ndb

from helpers.tbavideo_helper import TBAVideoHelper
from helpers.youtube_video_helper import YouTubeVideoHelper
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
    COMP_LEVELS_VERBOSE_FULL = {
        "qm": "Qualification",
        "ef": "Octo-finals",
        "qf": "Quarterfinals",
        "sf": "Semifinals",
        "f": "Finals",
    }
    COMP_LEVELS_PLAY_ORDER = {
        'qm': 1,
        'ef': 2,
        'qf': 3,
        'sf': 4,
        'f': 5,
    }

    alliances_json = ndb.StringProperty(required=True, indexed=False)  # JSON dictionary with alliances and scores.

    # {
    #   "red": {
    #     "teams": ["frc177", "frc195", "frc125"], # These are Team keys
    #     "surrogates": ["frc177", "frc195"],
    #     "score": 25
    #   },
    #   "blue": {
    #     "teams": ["frc433", "frc254", "frc222"],
    #     "surrogates": ["frc433"],
    #     "score": 12
    #   }
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
    year = ndb.IntegerProperty(required=True)
    match_number = ndb.IntegerProperty(required=True, indexed=False)
    no_auto_update = ndb.BooleanProperty(default=False, indexed=False)  # Set to True after manual update
    set_number = ndb.IntegerProperty(required=True, indexed=False)
    team_key_names = ndb.StringProperty(repeated=True)  # list of teams in Match, for indexing.
    time = ndb.DateTimeProperty()  # UTC time of scheduled start
    time_string = ndb.StringProperty(indexed=False)  # the time as displayed on FIRST's site (event's local time)
    actual_time = ndb.DateTimeProperty()  # UTC time of match actual start
    predicted_time = ndb.DateTimeProperty()  # UTC time of when we predict the match will start
    youtube_videos = ndb.StringProperty(repeated=True)  # list of Youtube IDs
    tba_videos = ndb.StringProperty(repeated=True)  # list of filetypes a TBA video exists for
    push_sent = ndb.BooleanProperty()  # has an upcoming match notification been sent for this match? None counts as False

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'key': set(),
            'event': set(),
            'team_keys': set(),
            'year': set(),
        }
        self._alliances = None
        self._score_breakdown = None
        self._tba_video = None
        self._winning_alliance = None
        self._youtube_videos = None
        self._updated_attrs = []  # Used in MatchManipulator to track what changed
        super(Match, self).__init__(*args, **kw)

    @property
    def alliances(self):
        """
        Lazy load alliances_json
        """
        if self._alliances is None:
            self._alliances = json.loads(self.alliances_json)

            for color in ['red', 'blue']:
                # score types are inconsistent in the db. convert everything to ints for now.
                score = self._alliances[color]['score']
                if score is None:
                    self._alliances[color]['score'] = -1
                else:
                    self._alliances[color]['score'] = int(score)

                # add surrogates if not present
                if 'surrogates' not in self._alliances[color]:
                    self._alliances[color]['surrogates'] = []

        return self._alliances

    @property
    def score_breakdown(self):
        """
        Lazy load score_breakdown_json
        """
        if self._score_breakdown is None and self.score_breakdown_json is not None:
            self._score_breakdown = json.loads(self.score_breakdown_json)

        return self._score_breakdown

    @property
    def winning_alliance(self):
        from helpers.event_helper import EventHelper
        from helpers.match_helper import MatchHelper
        if self._winning_alliance is None:
            if EventHelper.is_2015_playoff(self.event_key_name) and self.comp_level != 'f':
                return ''  # report all 2015 non finals matches as ties

            red_score = int(self.alliances['red']['score'])
            blue_score = int(self.alliances['blue']['score'])
            if red_score > blue_score:
                self._winning_alliance = 'red'
            elif blue_score > red_score:
                self._winning_alliance = 'blue'
            else:  # tie
                self._winning_alliance = MatchHelper.tiebreak_winner(self)
        return self._winning_alliance

    @property
    def event_key_name(self):
        return self.event.id()

    @property
    def team_keys(self):
        return [ndb.Key(Team, team_key_name) for team_key_name in self.team_key_names]

    @property
    def key_name(self):
        return self.renderKeyName(self.event_key_name, self.comp_level, self.set_number, self.match_number)

    @property
    def has_been_played(self):
        """If there are scores, it's been played"""
        for alliance in self.alliances:
            if (self.alliances[alliance]["score"] is None) or \
               (self.alliances[alliance]["score"] == -1):
                return False
        return True

    @property
    def verbose_name(self):
        from helpers.event_helper import EventHelper
        if self.comp_level == "qm" or self.comp_level == "f" or EventHelper.is_2015_playoff(self.event_key_name):
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
                if '?t=' in video:  # Treat ?t= the same as #t=
                    video = video.replace('?t=', '#t=')
                if '#t=' in video:
                    sp = video.split('#t=')
                    video_id = sp[0]
                    old_ts = sp[1]
                    total_seconds = YouTubeVideoHelper.time_to_seconds(old_ts)
                    video = '%s?start=%i' % (video_id, total_seconds)
                self._youtube_videos.append(video)
        return self._youtube_videos

    @property
    def videos(self):
        videos = []
        for v in self.youtube_videos_formatted:
            v = v.replace('?start=', '?t=')  # links must use ?t=
            videos.append({"type": "youtube", "key": v})
        if self.tba_video is not None:
            tba_path = self.tba_video.streamable_path
            if tba_path is not None:
                videos.append({"type": "tba", "key": tba_path})
        return videos

    @property
    def prediction_error_str(self):
        if self.actual_time and self.predicted_time:
            delta = self.actual_time - self.predicted_time
            if self.actual_time > self.predicted_time:
                return "{} early".format(delta)
            elif self.predicted_time > self.actual_time:
                return "{} late".format(delta)
            else:
                return "On Time"

    @property
    def schedule_error_str(self):
        if self.actual_time and self.time:
            delta = self.actual_time - self.time
            if self.actual_time > self.time:
                return "{} behind".format(delta)
            elif self.time > self.actual_time:
                return "{} ahead".format(delta)
            else:
                return "On Time"

    @classmethod
    def renderKeyName(self, event_key_name, comp_level, set_number, match_number):
        if comp_level == "qm":
            return "%s_qm%s" % (event_key_name, match_number)
        else:
            return "%s_%s%sm%s" % (event_key_name, comp_level, set_number, match_number)

    @classmethod
    def validate_key_name(self, match_key):
        key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+[0-9]?\_(?:qm|ef\dm|qf\dm|sf\dm|f\dm)\d+$')
        match = re.match(key_name_regex, match_key)
        return True if match else False
