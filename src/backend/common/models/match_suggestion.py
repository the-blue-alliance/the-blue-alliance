"""
Payload types for the GameDay match suggestion feed.

A cron (`/tasks/do/update_match_suggestions`) ranks upcoming matches across all
currently-live events and publishes the top N to the Firebase Realtime Database
node `match_suggestions`, where GameDay clients subscribe to them. Nothing is
persisted to Datastore -- the cron recomputes the feed every minute.

These are pydantic models rather than the TypedDicts used elsewhere in this
package so that `MatchSuggestions.model_json_schema()` can drive TypeScript
codegen for the client.

The Realtime Database bills per byte, so the per-suggestion fields -- repeated
once per match in the feed -- carry short `alias`es and are published with
`model_dump(by_alias=True)`. The root keys appear once per document, so they
stay readable. `populate_by_name=True` keeps the verbose names usable when
constructing these in Python.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.common.consts.comp_level import CompLevel
from backend.common.models.keys import EventKey, MatchKey


class MatchSuggestionComponents(BaseModel):
    """
    The individual scoring factors behind a suggestion, each normalized to [0, 1].

    `favorites` and `performance` are min-max normalized across the candidate pool
    of a single cron run, so they are only meaningful relative to their siblings in
    that same run. `significance` and `time_decay` are absolute.
    """

    model_config = ConfigDict(populate_by_name=True)

    favorites: float = Field(alias="f")
    significance: float = Field(alias="sig")
    time_decay: float = Field(alias="td")
    performance: float = Field(alias="p")


class MatchSuggestion(BaseModel):
    """
    A single suggested match, with enough denormalized context to render it
    without any further TBA API calls.
    """

    model_config = ConfigDict(populate_by_name=True)

    match_key: MatchKey = Field(alias="mk")
    event_key: EventKey = Field(alias="ek")
    event_name: str = Field(alias="en")
    event_short_name: Optional[str] = Field(default=None, alias="esn")

    comp_level: CompLevel = Field(alias="cl")
    set_number: int = Field(alias="sn")
    match_number: int = Field(alias="mn")
    # `Match.short_name`, e.g. "Q42" or "SF3"
    display_name: str = Field(alias="dn")

    # Bare team numbers, e.g. 254 -- `frc`-prefixed keys cost bytes per match
    red_team_numbers: List[int] = Field(alias="rt")
    blue_team_numbers: List[int] = Field(alias="bt")

    # Epoch seconds, UTC. The Realtime Database drops null children on write, so
    # these arrive at the client as absent rather than null.
    predicted_time: Optional[int] = Field(default=None, alias="pt")
    scheduled_time: Optional[int] = Field(default=None, alias="st")

    # 0-based; the stable ordering key for clients
    rank: int = Field(alias="r")
    score: float = Field(alias="sc")  # Weighted sum of `components`
    components: MatchSuggestionComponents = Field(alias="c")


class MatchSuggestions(BaseModel):
    """
    The root document published at the Firebase `match_suggestions` node.

    `suggestions` is keyed by match key rather than being a list so that the
    Realtime Database diffs individual children, letting clients react to
    `child_changed`/`child_removed` for one match instead of re-reading the
    whole feed. Read `rank` for ordering -- Realtime Database key order is
    lexicographic on match key, which is meaningless here.
    """

    updated_at: int  # Epoch seconds, UTC
    suggestions: Dict[MatchKey, MatchSuggestion] = Field(default_factory=dict)
