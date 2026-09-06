from datetime import datetime
from typing import List, Optional

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.helpers.insights_v2.clubs.hall_of_fame import (
    HallOfFameClubV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.media import Media
from backend.common.models.team import Team


def _put_event(
    event_key: str,
    year: int,
    event_type: EventType,
    start_date: Optional[datetime] = None,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        start_date=start_date,
    ).put()


def _put_award(
    event_key: str,
    year: int,
    team_keys: List[str],
    award_type: AwardType,
    event_type: EventType,
) -> None:
    Award(
        id=f"{event_key}_{award_type.value}",
        year=year,
        award_type_enum=award_type,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str=str(award_type),
        team_list=[ndb.Key(Team, k) for k in team_keys],
    ).put()


def _put_media(
    media_type: MediaType,
    foreign_key: str,
    tag: MediaTag,
    team_key: str,
    year: int,
) -> None:
    Media(
        id=Media.render_key_name(media_type, foreign_key),
        media_type_enum=media_type,
        media_tag_enum=[tag],
        references=[Media.create_reference("team", team_key)],
        year=year,
        foreign_key=foreign_key,
    ).put()


def _hof_award(event_key: str, year: int, team_keys: List[str]) -> None:
    _put_award(event_key, year, team_keys, AwardType.CHAIRMANS, EventType.CMP_FINALS)


def test_cmp_finals_chairmans_creates_entry(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _hof_award("2024cmptx", 2024, ["frc2486"])

    insights = compute_insights_for_year(0, [HallOfFameClubV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.key_name == "0_v2_clubs_hall_of_fame"
    assert insight.name == "hall_of_fame"
    assert insight.display_name == "Hall of Fame"
    assert insight.category == "clubs"
    assert insight.data["context_type"] == "hall_of_fame"
    assert insight.data["entries"] == [
        {
            "team_key": "frc2486",
            "event_added_key": "2024cmptx",
            "extra_context": {
                "year": 2024,
                "video": None,
                "presentation": None,
                "essay": None,
            },
        }
    ]


def test_extra_context_from_chairmans_media(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _hof_award("2024cmptx", 2024, ["frc2486"])
    _put_media(
        MediaType.YOUTUBE_VIDEO, "vid123", MediaTag.CHAIRMANS_VIDEO, "frc2486", 2024
    )
    _put_media(
        MediaType.YOUTUBE_VIDEO,
        "pres456",
        MediaTag.CHAIRMANS_PRESENTATION,
        "frc2486",
        2024,
    )
    _put_media(
        MediaType.EXTERNAL_LINK,
        "https://example.com/essay.pdf",
        MediaTag.CHAIRMANS_ESSAY,
        "frc2486",
        2024,
    )

    insights = compute_insights_for_year(0, [HallOfFameClubV2Calculator()])

    assert insights[0].data["entries"][0]["extra_context"] == {
        "year": 2024,
        "video": "https://youtu.be/vid123",
        "presentation": "https://youtu.be/pres456",
        "essay": "https://example.com/essay.pdf",
    }


def test_non_cmp_finals_chairmans_ignored(ndb_stub) -> None:
    _put_event("2024micmp", 2024, EventType.DISTRICT_CMP)
    _put_award("2024micmp", 2024, ["frc1"], AwardType.CHAIRMANS, EventType.DISTRICT_CMP)
    _put_event("2024arc", 2024, EventType.CMP_DIVISION)
    _put_award("2024arc", 2024, ["frc2"], AwardType.CHAIRMANS, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(0, [HallOfFameClubV2Calculator()])

    assert insights == []


def test_event_added_key_is_earliest(ndb_stub) -> None:
    _put_event("2011cmp", 2011, EventType.CMP_FINALS, start_date=datetime(2011, 4, 30))
    _hof_award("2011cmp", 2011, ["frc1114"])
    _put_event("2008cmp", 2008, EventType.CMP_FINALS, start_date=datetime(2008, 4, 19))
    _hof_award("2008cmp", 2008, ["frc1114"])

    insights = compute_insights_for_year(0, [HallOfFameClubV2Calculator()])

    entry = insights[0].data["entries"][0]
    assert entry["event_added_key"] == "2008cmp"
    assert entry["extra_context"]["year"] == 2008


def test_no_insight_for_specific_year(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _hof_award("2024cmptx", 2024, ["frc2486"])

    insights = compute_insights_for_year(2024, [HallOfFameClubV2Calculator()])

    assert insights == []


def test_entries_sorted_by_team_number(ndb_stub) -> None:
    _put_event("2019cmp", 2019, EventType.CMP_FINALS)
    _hof_award("2019cmp", 2019, ["frc1114"])
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _hof_award("2024cmptx", 2024, ["frc321"])

    insights = compute_insights_for_year(0, [HallOfFameClubV2Calculator()])

    team_keys = [e["team_key"] for e in insights[0].data["entries"]]
    assert team_keys == ["frc321", "frc1114"]
