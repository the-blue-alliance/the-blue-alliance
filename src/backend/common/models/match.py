import datetime
import json
import re
from typing import cast, Dict, List, Optional, Set

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts import comp_level
from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
    OPPONENT,
    TMatchWinner,
)
from backend.common.consts.comp_level import COMP_LEVELS_VERBOSE, CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import (
    DOUBLE_ELIM_4_MAPPING_INVERSE,
    DOUBLE_ELIM_MAPPING_INVERSE,
    PlayoffType,
)
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.models.alliance import MatchAlliance
from backend.common.models.cached_model import CachedModel
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, MatchKey, TeamKey, Year
from backend.common.models.match_score_breakdown import MatchScoreBreakdown
from backend.common.models.match_video import MatchVideo
from backend.common.models.tba_video import TBAVideo
from backend.common.models.team import Team


class Match(CachedModel):
    """
    Matches represent individual matches at Events.
    Matches have many Videos.
    Matches have many Alliances.
    key_name is like 2010ct_qm10 or 2010ct_sf1m2
    """

    alliances_json: str = ndb.TextProperty(
        required=True, indexed=False
    )  # JSON dictionary with alliances and scores.

    # {
    #   "red": {
    #     "teams": ["frc177", "frc195", "frc125"], # These are Team keys
    #     "surrogates": ["frc177", "frc195"],
    #     "dqs": [],
    #     "score": 25
    #   },
    #   "blue": {
    #     "teams": ["frc433", "frc254", "frc222"],
    #     "surrogates": ["frc433"],
    #     "dqs": ["frc433"],
    #     "score": 12
    #   }
    # }

    score_breakdown_json: Optional[str] = ndb.TextProperty(
        indexed=False
    )  # JSON dictionary with score breakdowns. Fields are those used for seeding. Varies by year.
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

    comp_level: CompLevel = cast(
        CompLevel,
        ndb.StringProperty(
            required=True,
            choices=set(comp_level.COMP_LEVELS),
            validator=CompLevel.ndb_validate,
        ),
    )
    event: ndb.Key = ndb.KeyProperty(kind=Event, required=True)
    year: Year = ndb.IntegerProperty(required=True)
    match_number = ndb.IntegerProperty(required=True, indexed=False)
    no_auto_update = ndb.BooleanProperty(
        default=False, indexed=False
    )  # Set to True after manual update
    set_number = ndb.IntegerProperty(required=True, indexed=False)
    # list of teams in Match, for indexing.
    team_key_names: List[TeamKey] = ndb.StringProperty(repeated=True)  # pyre-ignore[8]
    time = ndb.DateTimeProperty()  # UTC time of scheduled start
    time_string = ndb.TextProperty(
        indexed=False
    )  # the time as displayed on FIRST's site (event's local time)
    actual_time = ndb.DateTimeProperty()  # UTC time of match actual start
    predicted_time = (
        ndb.DateTimeProperty()
    )  # UTC time of when we predict the match will start
    post_result_time = (
        ndb.DateTimeProperty()
    )  # UTC time scores were shown to the audience
    # list of Youtube IDs
    youtube_videos: List[str] = ndb.StringProperty(repeated=True)  # pyre-ignore[8]
    # list of filetypes a TBA video exists for
    tba_videos: List[str] = ndb.StringProperty(repeated=True)  # pyre-ignore[8]
    push_sent = (
        ndb.BooleanProperty()
    )  # has an upcoming match notification been sent for this match? None counts as False
    tiebreak_match_key = ndb.KeyProperty(
        kind="Match"
    )  # Points to a match that was played to tiebreak this one
    display_name: str = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    _mutable_attrs: Set[str] = {
        "year",
        "no_auto_update",
        "time",
        "time_string",
        "actual_time",
        "predicted_time",
        "post_result_time",
        "push_sent",
        "tiebreak_match_key",
        "display_name",
    }

    _list_attrs: Set[str] = {
        "team_key_names",
    }

    _json_attrs: Set[str] = {
        "alliances_json",
        "score_breakdown_json",
    }

    _auto_union_attrs: Set[str] = {
        "tba_videos",
        "youtube_videos",
    }

    def __init__(self, *args, **kw) -> None:
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "key": set(),
            "event": set(),
            "team_keys": set(),
            "year": set(),
        }
        self._alliances: Optional[Dict[AllianceColor, MatchAlliance]] = None
        self._score_breakdown: Optional[MatchScoreBreakdown] = None
        self._tba_video: Optional[TBAVideo] = None
        self._winning_alliance: Optional[TMatchWinner] = None
        self._youtube_videos: Optional[List[str]] = None
        self._updated_attrs = []  # Used in MatchManipulator to track what changed
        super(Match, self).__init__(*args, **kw)

    @property
    def alliances(self) -> Dict[AllianceColor, MatchAlliance]:
        """
        Lazy load alliances_json
        """
        if self._alliances is None:
            alliances = json.loads(self.alliances_json)

            for color in ALLIANCE_COLORS:
                # score types are inconsistent in the db. convert everything to ints for now.
                score = alliances[color]["score"]
                if score is None:
                    alliances[color]["score"] = -1
                else:
                    alliances[color]["score"] = int(score)

                # add surrogates if not present
                if "surrogates" not in alliances[color]:
                    alliances[color]["surrogates"] = []

                # add dqs if not present
                if "dqs" not in alliances[color]:
                    alliances[color]["dqs"] = []

                # In elims, FIRST only reports the captain receiving a DQ
                # but we want to show it affecting the entire alliance
                if (
                    len(alliances[color]["dqs"]) != 0
                    and self.comp_level in comp_level.ELIM_LEVELS
                ):
                    alliances[color]["dqs"] = alliances[color]["teams"]
            self._alliances = alliances

        return none_throws(self._alliances)

    @alliances.setter
    def alliances(self, alliances: Dict[AllianceColor, MatchAlliance]):
        self._alliances = alliances
        self.alliances_json = json.dumps(alliances)

    @property
    def score_breakdown(self) -> Optional[MatchScoreBreakdown]:
        """
        Lazy load score_breakdown_json
        """
        if self._score_breakdown is None and self.score_breakdown_json is not None:
            try:
                score_breakdown = json.loads(none_throws(self.score_breakdown_json))
            except json.decoder.JSONDecodeError:
                return None

            if 'red' not in score_breakdown or 'blue' not in score_breakdown:
                # Handle some old matches with empty score breakdowns instead of None
                return None

            if self.has_been_played:
                # Add in RP calculations
                if self.year in {2016, 2017}:
                    for color in ALLIANCE_COLORS:
                        if self.comp_level == "qm":
                            rp_earned = 0
                            if self.winning_alliance == color:
                                rp_earned += 2
                            elif self.winning_alliance == "":
                                rp_earned += 1

                            if self.year == 2016:
                                if score_breakdown.get(color, {}).get(
                                    "teleopDefensesBreached"
                                ):
                                    rp_earned += 1
                                if score_breakdown.get(color, {}).get(
                                    "teleopTowerCaptured"
                                ):
                                    rp_earned += 1
                            elif self.year == 2017:
                                if score_breakdown.get(color, {}).get(
                                    "kPaRankingPointAchieved"
                                ):
                                    rp_earned += 1
                                if score_breakdown.get(color, {}).get(
                                    "rotorRankingPointAchieved"
                                ):
                                    rp_earned += 1
                            score_breakdown[color]["tba_rpEarned"] = rp_earned
                        else:
                            score_breakdown[color]["tba_rpEarned"] = None
                # Derive if bonus RP came from fouls
                if self.year == 2020:
                    for color in ALLIANCE_COLORS:
                        score_breakdown[color][
                            "tba_shieldEnergizedRankingPointFromFoul"
                        ] = (
                            score_breakdown[color]["shieldEnergizedRankingPoint"]
                            and not score_breakdown[color]["stage3Activated"]
                        )
                        score_breakdown[color]["tba_numRobotsHanging"] = sum(
                            [
                                (
                                    1
                                    if score_breakdown[color].get(
                                        "endgameRobot{}".format(i)
                                    )
                                    == "Hang"
                                    else 0
                                )
                                for i in range(1, 4)
                            ]
                        )
            self._score_breakdown = score_breakdown

        return self._score_breakdown

    @property
    def winning_alliance(self) -> TMatchWinner:
        from backend.common.helpers.event_helper import EventHelper
        from backend.common.helpers.match_tiebreakers import MatchTiebreakers

        if self._winning_alliance is None:
            if (
                EventHelper.is_2015_playoff(self.event_key_name)
                and self.comp_level != CompLevel.F
            ):
                return ""  # report all 2015 non finals matches as ties

            red_score = int(self.alliances[AllianceColor.RED]["score"])
            blue_score = int(self.alliances[AllianceColor.BLUE]["score"])
            if red_score > blue_score:
                self._winning_alliance = AllianceColor.RED
            elif blue_score > red_score:
                self._winning_alliance = AllianceColor.BLUE
            else:  # tie
                event = self.event.get()
                if (
                    event
                    and event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM
                    and event.event_type_enum == EventType.CMP_FINALS
                ):
                    self._winning_alliance = ""
                else:
                    self._winning_alliance = MatchTiebreakers.tiebreak_winner(self)
        return cast(TMatchWinner, none_throws(self._winning_alliance))

    @property
    def losing_alliance(self) -> TMatchWinner:
        winning_alliance = self.winning_alliance
        # No winning alliance means no losing alliance - either a tie, or 2015
        if winning_alliance == "":
            return ""

        return OPPONENT[cast(AllianceColor, winning_alliance)]

    @property
    def event_key_name(self) -> EventKey:
        return none_throws(self.event.string_id())

    @property
    def team_keys(self) -> List[ndb.Key]:
        return [ndb.Key(Team, team_key_name) for team_key_name in self.team_key_names]

    @property
    def key_name(self) -> MatchKey:
        return self.render_key_name(
            self.event_key_name, self.comp_level, self.set_number, self.match_number
        )

    @property
    def short_key(self) -> str:
        return none_throws(self.key.string_id()).split("_")[1]

    @property
    def has_been_played(self) -> bool:
        """If there are scores, it's been played"""
        for color in ALLIANCE_COLORS:
            if self.alliances[color]["score"] == -1:
                return False
        return True

    @property
    def verbose_name(self) -> str:
        if self.display_name:
            return self.display_name

        from backend.common.helpers.event_helper import EventHelper

        event = self.event.get()
        if (
            self.comp_level != CompLevel.QM
            and event
            and event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM
        ):
            if self.comp_level == CompLevel.F:
                return f"Finals {self.match_number}"

            # hard-code the match number to 1 for non-finals,
            # so we can render this correctly for replays
            match_num = DOUBLE_ELIM_MAPPING_INVERSE.get(
                (self.comp_level, self.set_number, 1)
            )
            if match_num is None:
                match_num = "?"

            replay_suffix = ""
            if self.match_number > 1:
                replay_suffix = f" (Play {self.match_number})"
            return f"Match {match_num}{replay_suffix}"

        elif (
            self.comp_level != "qm"
            and event
            and event.playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM
        ):
            if self.comp_level == "f":
                return f"Finals {self.match_number}"
            match_num = DOUBLE_ELIM_4_MAPPING_INVERSE.get(
                (self.comp_level, self.set_number, self.match_number)
            )
            if match_num is None:
                match_num = "?"
            return f"Match {match_num}"
        elif (
            self.comp_level == "qm"
            or self.comp_level == "f"
            or EventHelper.is_2015_playoff(self.event_key_name)
        ):
            return "%s %s" % (
                COMP_LEVELS_VERBOSE[self.comp_level],
                self.match_number,
            )
        else:
            return "%s %s Match %s" % (
                COMP_LEVELS_VERBOSE[self.comp_level],
                self.set_number,
                self.match_number,
            )

    @property
    def short_name(self) -> str:
        if self.comp_level == "qm":
            return "Q%s" % self.match_number
        elif self.comp_level == "f":
            return "F%s" % self.match_number
        else:
            return "%s%s-%s" % (
                self.comp_level.upper(),
                self.set_number,
                self.match_number,
            )

    @property
    def has_video(self) -> bool:
        return (len(self.youtube_videos) + len(self.tba_videos)) > 0

    @property
    def details_url(self) -> str:
        return "/match/%s" % self.key_name

    @property
    def tba_video(self) -> Optional[TBAVideo]:
        if len(self.tba_videos) > 0:
            if self._tba_video is None:
                self._tba_video = TBAVideo(
                    self.event_key_name, self.key_name, self.tba_videos
                )
        return self._tba_video

    @property
    def play_order(self) -> int:
        return (
            comp_level.COMP_LEVELS_PLAY_ORDER[self.comp_level] * 1000000
            + self.match_number * 1000
            + self.set_number
        )

    @property
    def name(self) -> str:
        return "%s" % (comp_level.COMP_LEVELS_VERBOSE[self.comp_level])

    @property
    def full_name(self) -> str:
        return "%s" % (comp_level.COMP_LEVELS_VERBOSE_FULL[self.comp_level])

    @property
    def youtube_videos_formatted(self) -> List[str]:
        """
        Get youtube video ids formatted for embedding
        """
        if self._youtube_videos is None:
            videos = []
            for video in self.youtube_videos:
                if "?t=" in video:  # Treat ?t= the same as #t=
                    video = video.replace("?t=", "#t=")
                if "#t=" in video:
                    sp = video.split("#t=")
                    video_id = sp[0]
                    old_ts = sp[1]
                    total_seconds = YouTubeVideoHelper.time_to_seconds(old_ts)
                    video = "%s?start=%i" % (video_id, total_seconds)
                videos.append(video)
            self._youtube_videos = videos
        return self._youtube_videos or []

    @property
    def videos(self) -> List[MatchVideo]:
        videos = []
        for v in self.youtube_videos_formatted:
            v = v.replace("?start=", "?t=")  # links must use ?t=
            videos.append({"type": "youtube", "key": v})
        tba_video = self.tba_video
        if tba_video is not None:
            tba_path = tba_video.streamable_path
            if tba_path is not None:
                videos.append({"type": "tba", "key": tba_path})
        return videos

    @property
    def prediction_error_str(self) -> Optional[str]:
        if self.actual_time and self.predicted_time:
            if self.actual_time > self.predicted_time:
                delta = self.actual_time - self.predicted_time
                s = int(delta.total_seconds())
                return "{:02}:{:02}:{:02} early".format(
                    s // 3600, s % 3600 // 60, s % 60
                )
            elif self.predicted_time > self.actual_time:
                delta = self.predicted_time - self.actual_time
                s = int(delta.total_seconds())
                return "{:02}:{:02}:{:02} late".format(
                    s // 3600, s % 3600 // 60, s % 60
                )
            else:
                return "On Time"
        return None

    @property
    def schedule_error_str(self) -> Optional[str]:
        if self.actual_time and self.time:
            if self.actual_time > self.time:
                delta = self.actual_time - self.time
                s = int(delta.total_seconds())
                return "{:02}:{:02}:{:02} behind".format(
                    s // 3600, s % 3600 // 60, s % 60
                )
            elif self.time > self.actual_time:
                delta = self.time - self.actual_time
                s = int(delta.total_seconds())
                return "{:02}:{:02}:{:02} ahead".format(
                    s // 3600, s % 3600 // 60, s % 60
                )
            else:
                return "On Time"
        return None

    @classmethod
    def render_key_name(
        cls,
        event_key_name: EventKey,
        comp_level: CompLevel,
        set_number: int,
        match_number: int,
    ) -> MatchKey:
        if comp_level == "qm":
            return "%s_qm%s" % (event_key_name, match_number)
        else:
            return "%s_%s%sm%s" % (event_key_name, comp_level, set_number, match_number)

    @classmethod
    def validate_key_name(cls, match_key: str) -> bool:
        key_name_regex = re.compile(
            r"^[1-9]\d{3}[a-z]+[0-9]*\_(?:qm|ef\d{1,2}m|qf\d{1,2}m|sf\d{1,2}m|f\dm)\d+$"
        )
        match = re.match(key_name_regex, match_key)
        return True if match else False

    def within_seconds(self, seconds: int) -> bool:
        """
        Returns: Boolean whether match started within specified seconds of now
        """
        return (
            self.actual_time
            and abs((datetime.datetime.now() - self.actual_time).total_seconds())
            <= seconds
        )
