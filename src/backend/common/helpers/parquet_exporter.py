import logging
from typing import Any, Dict, List, Optional

import pyarrow as pa

from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.models.team import Team

logger = logging.getLogger(__name__)


MATCH_SCHEMA = pa.schema(
    [
        pa.field("key", pa.string(), nullable=False),
        pa.field("event_key", pa.string(), nullable=False),
        pa.field("year", pa.int32(), nullable=False),
        pa.field("comp_level", pa.string(), nullable=False),
        pa.field("set_number", pa.int32(), nullable=False),
        pa.field("match_number", pa.int32(), nullable=False),
        pa.field("winning_alliance", pa.string()),
        pa.field("time", pa.timestamp("us", tz="UTC")),
        pa.field("actual_time", pa.timestamp("us", tz="UTC")),
        pa.field("predicted_time", pa.timestamp("us", tz="UTC")),
        pa.field("post_result_time", pa.timestamp("us", tz="UTC")),
        pa.field("red_score", pa.int32()),
        pa.field("blue_score", pa.int32()),
        pa.field("red_teams", pa.list_(pa.string())),
        pa.field("blue_teams", pa.list_(pa.string())),
        pa.field("red_surrogate_teams", pa.list_(pa.string())),
        pa.field("blue_surrogate_teams", pa.list_(pa.string())),
        pa.field("red_dq_teams", pa.list_(pa.string())),
        pa.field("blue_dq_teams", pa.list_(pa.string())),
    ]
)


TEAM_SCHEMA = pa.schema(
    [
        pa.field("key", pa.string(), nullable=False),
        pa.field("team_number", pa.int32(), nullable=False),
        pa.field("name", pa.string()),
        pa.field("nickname", pa.string()),
        pa.field("school_name", pa.string()),
        pa.field("city", pa.string()),
        pa.field("state_prov", pa.string()),
        pa.field("country", pa.string()),
        pa.field("postalcode", pa.string()),
        pa.field("website", pa.string()),
        pa.field("rookie_year", pa.int32()),
    ]
)


def flatten_match(match: Match) -> Dict[str, Any]:
    alliances = match.alliances
    red = alliances.get("red", {})
    blue = alliances.get("blue", {})

    red_score: Optional[int] = red.get("score")
    blue_score: Optional[int] = blue.get("score")
    if red_score == -1:
        red_score = None
    if blue_score == -1:
        blue_score = None

    try:
        winning = match.winning_alliance
    except Exception:
        winning = None

    return {
        "key": match.key.string_id(),
        "event_key": match.event_key_name,
        "year": match.year,
        "comp_level": match.comp_level,
        "set_number": match.set_number,
        "match_number": match.match_number,
        "winning_alliance": winning if winning else None,
        "time": match.time,
        "actual_time": match.actual_time,
        "predicted_time": match.predicted_time,
        "post_result_time": match.post_result_time,
        "red_score": red_score,
        "blue_score": blue_score,
        "red_teams": red.get("teams", []),
        "blue_teams": blue.get("teams", []),
        "red_surrogate_teams": red.get("surrogates", []),
        "blue_surrogate_teams": blue.get("surrogates", []),
        "red_dq_teams": red.get("dqs", []),
        "blue_dq_teams": blue.get("dqs", []),
    }


def flatten_team(team: Team) -> Dict[str, Any]:
    return {
        "key": team.key.string_id(),
        "team_number": team.team_number,
        "name": (team.name or "").strip() or None,
        "nickname": (team.nickname or "").strip() or None,
        "school_name": (team.school_name or "").strip() or None,
        "city": (team.city or "").strip() or None,
        "state_prov": (team.state_prov or "").strip() or None,
        "country": (team.country or "").strip() or None,
        "postalcode": (team.postalcode or "").strip() or None,
        "website": (team.website or "").strip() or None,
        "rookie_year": team.rookie_year,
    }


def matches_to_table(matches: List[Match]) -> pa.Table:
    rows = [flatten_match(m) for m in matches]
    if not rows:
        return MATCH_SCHEMA.empty_table()
    return pa.Table.from_pylist(rows, schema=MATCH_SCHEMA)


def teams_to_table(teams: List[Team]) -> pa.Table:
    rows = [flatten_team(t) for t in teams]
    if not rows:
        return TEAM_SCHEMA.empty_table()
    return pa.Table.from_pylist(rows, schema=TEAM_SCHEMA)
