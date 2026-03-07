import base64
import datetime
import json
import os
import random
from typing import List

from flask import redirect
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team

NUM_COMPLETED = 15
NUM_SCHEDULED = 8
NUM_UNSCHEDULED = 5
NUM_TEAMS = 21
MATCH_SPACING_MINUTES = 8


def seed_test_event() -> Response:
    now = datetime.datetime.now()
    year = now.year
    event_key = f"{year}test"

    # Create or reuse teams
    teams = _get_or_create_teams()

    # Create event
    event = Event(
        id=event_key,
        event_short="test",
        year=year,
        name="North Pole Showdown",
        event_type_enum=EventType.PRESEASON if now.month <= 2 else EventType.OFFSEASON,
        start_date=datetime.datetime(year, now.month, now.day)
        - datetime.timedelta(days=1),
        end_date=datetime.datetime(year, now.month, now.day)
        + datetime.timedelta(days=1),
        official=False,
        webcast_json=json.dumps(
            [
                {"type": "twitch", "channel": "firstinspires"},
                {"type": "youtube", "channel": "dQw4w9WgXcQ"},
            ]
        ),
    )
    EventManipulator.createOrUpdate(event)

    # Create matches
    matches: List[Match] = []

    total_completed_time = now - datetime.timedelta(
        minutes=NUM_COMPLETED * MATCH_SPACING_MINUTES
    )

    # Completed matches (qm1 - qm15)
    for i in range(1, NUM_COMPLETED + 1):
        red_teams, blue_teams = _teams_for_match(teams, i)
        red_score = random.randint(20, 150)
        blue_score = random.randint(20, 150)
        match_time = total_completed_time + datetime.timedelta(
            minutes=(i - 1) * MATCH_SPACING_MINUTES
        )
        match = Match(
            id=Match.render_key_name(event_key, CompLevel.QM, 1, i),
            event=ndb.Key(Event, event_key),
            year=year,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=i,
            team_key_names=[f"frc{t}" for t in red_teams + blue_teams],
            alliances_json=json.dumps(
                {
                    "red": {
                        "teams": [f"frc{t}" for t in red_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": red_score,
                    },
                    "blue": {
                        "teams": [f"frc{t}" for t in blue_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": blue_score,
                    },
                }
            ),
            time=match_time,
            actual_time=match_time,
        )
        matches.append(match)

    # Scheduled matches (qm16 - qm23)
    # Q21, Q22, Q23 get predicted times that drift from schedule by 2, 5,
    # and 10 minutes respectively, to test "(est.)" display in the app.
    predicted_time_offsets = {21: 2, 22: 5, 23: 10}  # match_number -> minutes
    scheduled_start = now + datetime.timedelta(minutes=10)
    for i in range(NUM_COMPLETED + 1, NUM_COMPLETED + NUM_SCHEDULED + 1):
        red_teams, blue_teams = _teams_for_match(teams, i)
        match_time = scheduled_start + datetime.timedelta(
            minutes=(i - NUM_COMPLETED - 1) * MATCH_SPACING_MINUTES
        )
        predicted_time = None
        if i in predicted_time_offsets:
            predicted_time = match_time + datetime.timedelta(
                minutes=predicted_time_offsets[i]
            )
        match = Match(
            id=Match.render_key_name(event_key, CompLevel.QM, 1, i),
            event=ndb.Key(Event, event_key),
            year=year,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=i,
            team_key_names=[f"frc{t}" for t in red_teams + blue_teams],
            alliances_json=json.dumps(
                {
                    "red": {
                        "teams": [f"frc{t}" for t in red_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": -1,
                    },
                    "blue": {
                        "teams": [f"frc{t}" for t in blue_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": -1,
                    },
                }
            ),
            time=match_time,
            predicted_time=predicted_time,
        )
        matches.append(match)

    # Unscheduled matches (qm24 - qm28)
    unscheduled_start = NUM_COMPLETED + NUM_SCHEDULED + 1
    for i in range(unscheduled_start, unscheduled_start + NUM_UNSCHEDULED):
        red_teams, blue_teams = _teams_for_match(teams, i)
        match = Match(
            id=Match.render_key_name(event_key, CompLevel.QM, 1, i),
            event=ndb.Key(Event, event_key),
            year=year,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=i,
            team_key_names=[f"frc{t}" for t in red_teams + blue_teams],
            alliances_json=json.dumps(
                {
                    "red": {
                        "teams": [f"frc{t}" for t in red_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": -1,
                    },
                    "blue": {
                        "teams": [f"frc{t}" for t in blue_teams],
                        "surrogates": [],
                        "dqs": [],
                        "score": -1,
                    },
                }
            ),
        )
        matches.append(match)

    MatchManipulator.createOrUpdate(matches)

    # Create EventTeam records
    team_numbers = {t.team_number for t in teams}
    event_teams = [
        EventTeam(
            id=f"{event_key}_frc{num}",
            event=ndb.Key(Event, event_key),
            team=ndb.Key(Team, f"frc{num}"),
            year=year,
        )
        for num in team_numbers
    ]
    EventTeamManipulator.createOrUpdate(event_teams)

    return redirect(f"/event/{event_key}")


def _get_or_create_teams() -> List[Team]:
    existing = Team.query().fetch(limit=NUM_TEAMS)
    if len(existing) >= 6:
        return existing[:NUM_TEAMS]

    # Create placeholder teams
    teams = []
    for i in range(1, NUM_TEAMS + 1):
        team = Team(
            id=f"frc{i}",
            team_number=i,
            nickname=f"Team {i}",
        )
        teams.append(team)
    TeamManipulator.createOrUpdate(teams)
    return teams


def seed_test_team() -> Response:
    now = datetime.datetime.now()
    year = now.year

    team = Team(
        id="frc2",
        team_number=2,
        nickname="The Reindeer",
        name="North Pole High School & The Reindeer",
        city="North Pole",
        state_prov="AK",
        country="USA",
        school_name="North Pole High School",
        website="https://www.thebluealliance.com/team/2",
        rookie_year=1997,
        motto="Dasher, Dancer, Prancer, Vixen!",
    )
    TeamManipulator.createOrUpdate(team)

    team_ref = Media.create_reference("team", "frc2")
    avatar_foreign_key = f"avatar_{year}_frc2"

    # Load avatar image from test_data/reindeer_avatar.png
    avatar_path = os.path.join(
        os.path.dirname(__file__), "test_data", "reindeer_avatar.png"
    )
    avatar_b64 = ""
    if os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            avatar_b64 = base64.b64encode(f.read()).decode("ascii")

    media_list = [
        Media(
            id=Media.render_key_name(MediaType.AVATAR, avatar_foreign_key),
            media_type_enum=MediaType.AVATAR,
            foreign_key=avatar_foreign_key,
            year=year,
            references=[team_ref],
            details_json=json.dumps({"base64Image": avatar_b64}),
        ),
        Media(
            id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, "dQw4w9WgXcQ"),
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key="dQw4w9WgXcQ",
            year=year,
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.IMGUR, "aF8T5ZE"),
            media_type_enum=MediaType.IMGUR,
            foreign_key="aF8T5ZE",
            year=year,
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.INSTAGRAM_IMAGE, "B9ZUsERhIWi"),
            media_type_enum=MediaType.INSTAGRAM_IMAGE,
            foreign_key="B9ZUsERhIWi",
            year=year,
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.YOUTUBE_CHANNEL, "bobcatrobotics"),
            media_type_enum=MediaType.YOUTUBE_CHANNEL,
            foreign_key="bobcatrobotics",
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.INSTAGRAM_PROFILE, "bobcatrobotics"),
            media_type_enum=MediaType.INSTAGRAM_PROFILE,
            foreign_key="bobcatrobotics",
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.FACEBOOK_PROFILE, "thebluealliance"),
            media_type_enum=MediaType.FACEBOOK_PROFILE,
            foreign_key="thebluealliance",
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.TWITTER_PROFILE, "thebluealliance"),
            media_type_enum=MediaType.TWITTER_PROFILE,
            foreign_key="thebluealliance",
            references=[team_ref],
        ),
        Media(
            id=Media.render_key_name(MediaType.GITHUB_PROFILE, "the-blue-alliance"),
            media_type_enum=MediaType.GITHUB_PROFILE,
            foreign_key="the-blue-alliance",
            references=[team_ref],
        ),
    ]
    MediaManipulator.createOrUpdate(media_list)

    return redirect("/team/2")


def _teams_for_match(teams: List[Team], match_number: int) -> tuple:
    """Cycle through teams for match assignments, 6 per match."""
    n = len(teams)
    offset = ((match_number - 1) * 6) % n
    indices = [(offset + j) % n for j in range(6)]
    team_nums = [teams[i].team_number for i in indices]
    return team_nums[:3], team_nums[3:]
