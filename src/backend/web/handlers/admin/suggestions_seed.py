import datetime
import json
import random
import string
from typing import List, Optional, Tuple

from flask import abort, request
from google.appengine.ext import ndb

from backend.common.consts.account_permission import SUGGESTION_PERMISSIONS
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType, PROFILE_URLS
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SUGGESTION_TYPES, TYPE_NAMES
from backend.common.consts.webcast_type import WebcastType
from backend.common.environment.environment import Environment
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.profiled_render import render_template

SEED_AUTHOR_ACCOUNT_ID = "suggestion-seed-bot"

# Real media so seeded suggestions preview properly in review UIs. Video
# suggestion keys are deterministic per video+target, so repeat seeding walks
# this pool of embeddable FIRST game animations and only falls back to a
# random (unavailable) ID once the pool is exhausted.
SEED_YOUTUBE_VIDEO_IDS = [
    "_fybREErgyM",  # 2026 REBUILT
    "9keeDyFxzY4",  # 2024 CRESCENDO
    "0zpflsYc4PA",  # 2023 CHARGED UP
    "LgniEjI9cCM",  # 2022 RAPID REACT
]
SEED_YOUTUBE_VIDEO_ID = SEED_YOUTUBE_VIDEO_IDS[0]
SEED_TWITCH_CHANNEL = "firstinspires"
SEED_IMGUR_IMAGE_ID = "2xhn4BX"
SEED_INSTAGRAM_POST_ID = "C4bhT7FsmAW"
# Real FRC-community GitHub orgs; repeat seeding walks the pool for variety
SEED_GITHUB_USERS = [
    "the-blue-alliance",
    "wpilibsuite",
    "frc971",
    "frc1678",
    "team254",
    "Mechanical-Advantage",
]
SEED_GITHUB_USER = SEED_GITHUB_USERS[0]
# (media_type, foreign_key, site_name, profile_url override or None)
SEED_SOCIAL_PROFILES = [
    (MediaType.FACEBOOK_PROFILE, "thebluealliance", "Facebook", None),
    (
        MediaType.TWITTER_PROFILE,
        "thebluealliance",
        "X",
        "https://x.com/thebluealliance",
    ),
    (MediaType.INSTAGRAM_PROFILE, "the_blue_alliance", "Instagram", None),
    (MediaType.YOUTUBE_CHANNEL, "@FIRSTRoboticsCompetition", "YouTube", None),
    # Malformed on purpose: personal-profile and video links, not usernames,
    # to exercise the review UI's malformed-submission warnings
    (
        MediaType.FACEBOOK_PROFILE,
        "profile.php?id=100064531607957",
        "Facebook",
        None,
    ),
    (MediaType.YOUTUBE_CHANNEL, "watch?v=_fybREErgyM", "YouTube", None),
]

# Mocked entities the seeds target by default
SEED_TEAM_KEY = "frc2"
SEED_TEAM_NICKNAME = "The Reindeer"
SEED_EVENT_NAME = "North Pole Regional"
SEED_EVENT_SHORT_NAME = "North Pole"
SEED_EVENT_SHORT = "np"


def _random_id(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def _seed_author() -> Account:
    return Account.get_or_insert(
        SEED_AUTHOR_ACCOUNT_ID,
        email="seed-bot@thebluealliance.com",
        nickname="Suggestion Seed Bot",
        display_name="Suggestion Seed Bot",
        registered=True,
        permissions=[],
    )


def _ensure_team(team_key: str) -> Tuple[Team, bool]:
    team = Team.get_by_id(team_key)
    if team:
        # The seed team always presents as the mocked data team, even if the
        # dev datastore already has an entity for it
        if team_key == SEED_TEAM_KEY and team.nickname != SEED_TEAM_NICKNAME:
            team.nickname = SEED_TEAM_NICKNAME
            team.name = SEED_TEAM_NICKNAME
            team = TeamManipulator.createOrUpdate(team)
        return team, False
    nickname = SEED_TEAM_NICKNAME if team_key == SEED_TEAM_KEY else "Seeded Test Team"
    team = Team(
        id=team_key,
        team_number=int(team_key[3:]),
        nickname=nickname,
        name=nickname,
        city="North Pole",
        state_prov="AK",
        country="USA",
    )
    return TeamManipulator.createOrUpdate(team), True


def _ensure_event(event_key: str) -> Tuple[Optional[Event], bool]:
    event = Event.get_by_id(event_key)
    if event:
        if event.event_short == SEED_EVENT_SHORT and event.name != SEED_EVENT_NAME:
            event.name = SEED_EVENT_NAME
            event.short_name = SEED_EVENT_SHORT_NAME
            event = EventManipulator.createOrUpdate(event)
        return event, False
    if not Event.validate_key_name(event_key):
        return None, False
    year = int(event_key[:4])
    start = datetime.datetime(year, 10, 1)
    event = Event(
        id=event_key,
        name=SEED_EVENT_NAME,
        short_name=SEED_EVENT_SHORT_NAME,
        event_short=event_key[4:],
        event_type_enum=EventType.OFFSEASON,
        year=year,
        start_date=start,
        end_date=start + datetime.timedelta(days=1),
        official=False,
        city="North Pole",
        state_prov="AK",
        country="USA",
        venue="Santa's Workshop",
        venue_address="Santa's Workshop, North Pole, AK, USA",
        website="https://www.thebluealliance.com",
        webcast_json="",
    )
    return EventManipulator.createOrUpdate(event), True


def _ensure_match(match_key: str) -> Tuple[Optional[Match], bool]:
    match = Match.get_by_id(match_key)
    if match:
        return match, False
    event_key = match_key.split("_")[0]
    event, _ = _ensure_event(event_key)
    if event is None:
        return None, False
    match = Match(
        id=match_key,
        event=ndb.Key(Event, event_key),
        year=event.year,
        comp_level="qm",
        set_number=1,
        match_number=int(match_key.split("qm")[-1]) if "qm" in match_key else 1,
        team_key_names=[
            SEED_TEAM_KEY,
            "frc1678",
            "frc973",
            "frc846",
            "frc2135",
            "frc971",
        ],
        alliances_json=json.dumps(
            {
                "red": {"score": 100, "teams": [SEED_TEAM_KEY, "frc1678", "frc973"]},
                "blue": {"score": 90, "teams": ["frc846", "frc2135", "frc971"]},
            }
        ),
    )
    return MatchManipulator.createOrUpdate(match), True


def _seed_media_suggestion(
    author: Account, target_model: str, team_key: str
) -> Tuple[str, str]:
    """Seed team media (image/video/instagram), social media, or CAD suggestions."""
    foreign_key = f"seed{_random_id(6)}"
    year = datetime.datetime.now().year
    contents_list = []
    if target_model == "media":
        # Media URLs render from foreign_key, so real media previews properly.
        # Suggestions get auto ids, so repeat seeding of the same media is fine.
        contents_list = [
            {
                "media_type_enum": int(MediaType.IMGUR),
                "foreign_key": SEED_IMGUR_IMAGE_ID,
                "reference_type": "team",
                "reference_key": team_key,
                "year": year,
                "details_json": json.dumps(
                    {"image_partial": f"{SEED_IMGUR_IMAGE_ID}l.jpg"}
                ),
                "site_name": "Imgur",
            },
            {
                "media_type_enum": int(MediaType.YOUTUBE_VIDEO),
                "foreign_key": SEED_YOUTUBE_VIDEO_ID,
                "reference_type": "team",
                "reference_key": team_key,
                "year": year,
                "site_name": "YouTube",
            },
            {
                "media_type_enum": int(MediaType.INSTAGRAM_IMAGE),
                "foreign_key": SEED_INSTAGRAM_POST_ID,
                "reference_type": "team",
                "reference_key": team_key,
                "year": year,
                "site_name": "Instagram",
            },
        ]
    elif target_model == "social-media":
        # One of each platform per round, all real profiles. GitHub cycles
        # through real orgs so repeat seeding shows varied live cards.
        pending_social = SuggestionFetcher.count_async(
            SuggestionState.REVIEW_PENDING, "social-media"
        ).get_result()
        github_user = SEED_GITHUB_USERS[pending_social % len(SEED_GITHUB_USERS)]
        contents_list = [
            {
                "media_type_enum": int(MediaType.GITHUB_PROFILE),
                "foreign_key": github_user,
                "reference_type": "team",
                "reference_key": team_key,
                "is_social": True,
                "site_name": "GitHub",
                "profile_url": f"https://github.com/{github_user}",
            }
        ] + [
            {
                "media_type_enum": int(media_type),
                "foreign_key": profile_key,
                "reference_type": "team",
                "reference_key": team_key,
                "is_social": True,
                "site_name": site_name,
                "profile_url": profile_url
                or PROFILE_URLS[media_type].format(profile_key),
            }
            for media_type, profile_key, site_name, profile_url in SEED_SOCIAL_PROFILES
        ]
    else:  # robot / CAD
        contents_list = [
            {
                "media_type_enum": int(MediaType.GRABCAD),
                "foreign_key": foreign_key,
                "reference_type": "team",
                "reference_key": team_key,
                "year": year,
                "details_json": json.dumps(
                    {
                        "model_name": f"Seeded CAD Model {foreign_key}",
                        "model_description": "A seeded robot CAD model for moderation testing",
                        "model_image": f"https://i.imgur.com/{SEED_IMGUR_IMAGE_ID}l.jpg",
                        "model_created": datetime.datetime.now().isoformat(),
                    }
                ),
            }
        ]
    for suggestion_contents in contents_list:
        suggestion = Suggestion(
            author=author.key,
            target_model=target_model,
            target_key=team_key,
        )
        suggestion.contents = suggestion_contents
        suggestion.put()
    return SuggestionCreationStatus.SUCCESS, foreign_key


def _seed_event_media_suggestion(author: Account, event_key: str) -> str:
    status = SuggestionCreationStatus.SUCCESS
    for youtube_id in (*SEED_YOUTUBE_VIDEO_IDS, _random_youtube_id()):
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            author.key,
            f"https://www.youtube.com/watch?v={youtube_id}",
            event_key,
        ).get_result()
        if status == SuggestionCreationStatus.SUCCESS:
            break
    return status


def _random_youtube_id() -> str:
    # YouTube IDs are 11 chars; a random one previews as unavailable but
    # keeps repeat seeding unique once the real video is taken
    return _random_id(11)


def _seed_webcast_suggestion(author: Account, event_key: str) -> str:
    suggestion = Suggestion(
        author=author.key,
        target_model="event",
        target_key=event_key,
    )
    suggestion.contents = {
        "webcast_url": f"https://twitch.tv/{SEED_TWITCH_CHANNEL}",
        "webcast_dict": {
            "type": WebcastType.TWITCH,
            "channel": SEED_TWITCH_CHANNEL,
        },
        "webcast_date": "",
    }
    suggestion.put()
    return SuggestionCreationStatus.SUCCESS


def _seed_offseason_suggestion(author: Account) -> str:
    year = datetime.datetime.now().year
    suffix = _random_id(4)
    status, _ = SuggestionCreator.createOffseasonEventSuggestion(
        author_account_key=author.key,
        name=f"Seeded Offseason Invitational {suffix}",
        start_date=f"{year}-10-15",
        end_date=f"{year}-10-16",
        website="https://www.thebluealliance.com",
        venue_name="Seeded Venue",
        address="123 Fake St",
        city="San Jose",
        state="CA",
        country="USA",
    )
    return status


def _seed_apiwrite_suggestion(author: Account, event_key: str) -> str:
    return SuggestionCreator.createApiWriteSuggestion(
        author_account_key=author.key,
        event_key=event_key,
        affiliation=f"Seeded Robotics {_random_id(4)}",
        auth_types=[
            int(AuthType.EVENT_TEAMS),
            int(AuthType.EVENT_MATCHES),
            int(AuthType.MATCH_VIDEO),
        ],
    )


def _pending_counts() -> dict:
    futures = {
        suggestion_type: SuggestionFetcher.count_async(
            SuggestionState.REVIEW_PENDING, suggestion_type
        )
        for suggestion_type in SUGGESTION_TYPES
    }
    return {
        suggestion_type: future.get_result()
        for suggestion_type, future in futures.items()
    }


def _default_keys() -> Tuple[str, str, str]:
    year = datetime.datetime.now().year
    event_key = f"{year}{SEED_EVENT_SHORT}"
    return SEED_TEAM_KEY, event_key, f"{event_key}_qm1"


def _abort_in_prod() -> None:
    # Seeding fabricates suggestions and grants review permissions; it is
    # dev-environment tooling and must never run against production data
    if Environment.is_prod():
        abort(404)


def suggestion_seed_get() -> str:
    _abort_in_prod()
    team_key, event_key, match_key = _default_keys()
    template_values = {
        "type_names": TYPE_NAMES,
        "pending_counts": _pending_counts(),
        "default_team_key": team_key,
        "default_event_key": event_key,
        "default_match_key": match_key,
    }
    return render_template("admin/suggestion_seed.html", template_values)


def suggestion_seed_post() -> str:
    _abort_in_prod()
    author = _seed_author()
    types = request.form.getlist("types")
    team_key = request.form.get("team_key") or _default_keys()[0]
    event_key = request.form.get("event_key") or _default_keys()[1]
    match_key = request.form.get("match_key") or _default_keys()[2]

    results: List[Tuple[str, str]] = []

    # Make sure targets exist so accepts work on an empty dev datastore
    _, team_created = _ensure_team(team_key)
    if team_created:
        results.append(("setup", f"Created team {team_key}"))
    event, event_created = _ensure_event(event_key)
    if event_created:
        results.append(("setup", f"Created event {event_key}"))
    match, match_created = _ensure_match(match_key)
    if match_created:
        results.append(("setup", f"Created match {match_key}"))

    for suggestion_type in types:
        if suggestion_type not in SUGGESTION_TYPES:
            results.append((suggestion_type, "unknown type, skipped"))
            continue
        if suggestion_type in ("media", "social-media", "robot"):
            status, _ = _seed_media_suggestion(author, suggestion_type, team_key)
        elif suggestion_type == "event_media":
            if event is None:
                status = f"skipped: event {event_key} unavailable"
            else:
                status = _seed_event_media_suggestion(author, event_key)
        elif suggestion_type == "event":
            if event is None:
                status = f"skipped: event {event_key} unavailable"
            else:
                status = _seed_webcast_suggestion(author, event_key)
        elif suggestion_type == "match":
            if match is None:
                status = f"skipped: match {match_key} unavailable"
            else:
                status = SuggestionCreationStatus.VIDEO_EXISTS
                for youtube_id in (*SEED_YOUTUBE_VIDEO_IDS, _random_youtube_id()):
                    status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
                        author.key, youtube_id, match_key
                    )
                    if status == SuggestionCreationStatus.SUCCESS:
                        break
        elif suggestion_type == "offseason-event":
            status = _seed_offseason_suggestion(author)
        else:  # api_auth_access
            if event is None:
                status = f"skipped: event {event_key} unavailable"
            else:
                status = _seed_apiwrite_suggestion(author, event_key)
        results.append((suggestion_type, str(status)))

    grant_email = request.form.get("grant_email")
    if grant_email:
        accounts = Account.query(Account.email == grant_email).fetch()
        if accounts:
            account = accounts[0]
            account.permissions = list(SUGGESTION_PERMISSIONS)
            account.put()
            results.append(
                ("permissions", f"Granted all review permissions to {grant_email}")
            )
        else:
            results.append(
                ("permissions", f"No account found for {grant_email} (log in first)")
            )

    team_key_default, event_key_default, match_key_default = _default_keys()
    template_values = {
        "type_names": TYPE_NAMES,
        "pending_counts": _pending_counts(),
        "default_team_key": team_key_default,
        "default_event_key": event_key_default,
        "default_match_key": match_key_default,
        "results": results,
    }
    return render_template("admin/suggestion_seed.html", template_values)
