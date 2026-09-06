from typing import Optional

import pytest

from backend.common.consts.event_type import EventType
from backend.common.helpers.similar_event_helper import (
    MAX_SIMILAR_EVENTS,
    name_similarity,
    SimilarEventHelper,
    SIMILARITY_THRESHOLD,
)
from backend.common.models.event import Event


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub):
    yield


def make_event(
    key: str,
    name: str,
    city: str = "Anytown",
    state_prov: str = "NY",
    country: str = "USA",
    venue: Optional[str] = None,
) -> Event:
    return Event(
        id=key,
        year=int(key[:4]),
        event_short=key[4:],
        event_type_enum=EventType.OFFSEASON,
        name=name,
        city=city,
        state_prov=state_prov,
        country=country,
        venue=venue,
    )


# Real year-over-year renames pulled from TBA. Each entry is
# (last year's event, this year's suggestion) for the same recurring event.
RENAMED_EVENTS = [
    pytest.param(
        make_event("2024sccol", "SCRIW XIII", "Columbia", "SC"),
        make_event(
            "2025sccol",
            "South Carolina Robotics Invitational & Workshops",
            "Colunbia",
            "SC",
        ),
        id="acronym_expanded",
    ),
    pytest.param(
        make_event("2024wiwi", "Where is Wolcott Invitational", "Wolcott", "CT"),
        make_event("2025wiwi", "WIWI", "Wolcott", "CT"),
        id="acronym_abbreviated",
    ),
    pytest.param(
        make_event(
            "2017gagr",
            "Georgia Robotics Invitational Tournament & Showcase",
            "Gainesville",
            "GA",
        ),
        make_event("2018gagr", "GRITS", "Roswell", "GA"),
        id="acronym_across_cities",
    ),
    pytest.param(
        make_event("2023ncrc", "NCRC", "Cranberry Township", "PA"),
        make_event(
            "2024ncrc", "North Catholic Robotics Competition", "Cranberry Twp", "PA"
        ),
        id="acronym_with_generic_words",
    ),
    pytest.param(
        make_event(
            "2016ncth", "THOR - Thundering Herd of Robots", "North Carolina", "NC"
        ),
        make_event("2017ncth", "THOR @ UNC Pembroke", "Pembroke", "NC"),
        id="acronym_kept_subtitle_replaced",
    ),
    pytest.param(
        make_event("2018gagr", "GRITS", "Roswell", "GA"),
        make_event("2019gagr", "GRITS – Deep Space", "Marietta", "GA"),
        id="game_name_appended",
    ),
    pytest.param(
        make_event("2021cabl", "Beach Blitz", "Aliso Viejo", "CA"),
        make_event(
            "2022cabl",
            "Beach Blitz presented by the Gene Haas Foundation",
            "Mission Viejo",
            "CA",
        ),
        id="sponsor_appended",
    ),
    pytest.param(
        make_event("2024tnkno", "Tennessee Valley Fair Robo-Rodeo", "Knoxville", "TN"),
        make_event("2025tnkno", "Robo-Rodeo at the TN Valley Fair", "Knoxville", "TN"),
        id="words_reordered",
    ),
    pytest.param(
        make_event("2022scriw", "SCRIW XI", "Columbia", "SC"),
        make_event(
            "2023scriw",
            "SCRIW XII (South Carolina Robotics Invitational and Workshops)",
            "Columbia",
            "SC",
        ),
        id="roman_numeral_edition",
    ),
    pytest.param(
        make_event(
            "2016iroc", "IROC - ILITE Robotics Offseason Challenge", "Virginia", "VA"
        ),
        make_event("2017iroc", "IROC", "Haymarket", "VA"),
        id="subtitle_dropped",
    ),
    pytest.param(
        make_event("2018mirc", "ROBO-CON FRC Off Season Competition ", "Lapeer", "MI"),
        make_event("2019mirc", "ROBO-CON", "Lapeer", "MI"),
        id="boilerplate_dropped",
    ),
    pytest.param(
        make_event(
            "2021scsc",
            "South Carolina Robotics & Practical Off-Season",
            "Columbia",
            "SC",
        ),
        make_event("2022scsc", "SCRAP - Friday", "Sumter", "SC"),
        id="acronym_of_an_ampersand_and_a_shortened_name",
    ),
    pytest.param(
        make_event(
            "2024mncc",
            "Central Minnesota Robotics Conference Championship",
            "Becker",
            "MN",
        ),
        make_event("2025cmrc", "CMRC Championship", "Becker", "MN"),
        id="acronym_of_the_front_of_a_name",
    ),
    pytest.param(
        make_event("2024txri", "Texas Robotics Invitational", "Houston", "TX"),
        make_event("2025txhou1", "Texas Robotics Invitational", "Houston", "TX"),
        id="same_name_new_event_short",
    ),
]

# Real pairs of *different* offseason events whose names collide on the generic
# robotics vocabulary that shows up in nearly every FRC event name.
UNRELATED_EVENTS = [
    pytest.param(
        make_event("2023txri", "Texas Robotics Invitational", "Houston", "TX"),
        make_event("2024wiwi", "Where is Wolcott Invitational", "Wolcott", "CT"),
        id="shared_invitational",
    ),
    pytest.param(
        make_event(
            "2018marc", "Michigan Advanced Robotics Competition", "Monroe", "MI"
        ),
        make_event("2019inirr", "Indiana Robotics Invitational", "Indianapolis", "IN"),
        id="shared_robotics",
    ),
    pytest.param(
        make_event("2019nhbb", "Battle of the Bay", "Alton", "NH"),
        make_event("2024casd", "Battle at the Border", "San Diego", "CA"),
        id="shared_battle",
    ),
    pytest.param(
        make_event(
            "2023aztem",
            "Sanghi Foundation Arizona FRC State Championship",
            "Tempe",
            "AZ",
        ),
        make_event("2024ohna", "Ohio FRC State Championship", "New Albany", "OH"),
        id="shared_state_championship",
    ),
    pytest.param(
        make_event("2018ohsh", "Shawshank Showdown", "Mansfield", "OH"),
        make_event("2019flsc", "Space Coast Showdown", "Rockledge", "FL"),
        id="shared_showdown",
    ),
    pytest.param(
        make_event("2024ndse", "STEM Expo", "West Fargo", "ND"),
        make_event("2025txsg", "STEM Gals", "Rockwall", "TX"),
        id="shared_stem",
    ),
    pytest.param(
        make_event("2018mnwcw", "West Central Week 0", "Willmar", "MN"),
        make_event("2019mibd", "Dickinson Center Week 0", "Livonia", "MI"),
        id="shared_week_zero",
    ),
]


@pytest.mark.parametrize("last_year_event, suggested_event", RENAMED_EVENTS)
def test_renamed_event_is_surfaced(
    last_year_event: Event, suggested_event: Event
) -> None:
    assert SimilarEventHelper.similar_events(suggested_event, [last_year_event]) == [
        last_year_event
    ]


@pytest.mark.parametrize("existing_event, suggested_event", UNRELATED_EVENTS)
def test_unrelated_event_is_not_surfaced(
    existing_event: Event, suggested_event: Event
) -> None:
    assert SimilarEventHelper.similar_events(suggested_event, [existing_event]) == []


def test_no_events_to_compare_against() -> None:
    suggested = make_event("2025nyny", "Robot Rumble")
    assert SimilarEventHelper.similar_events(suggested, []) == []


def test_best_match_is_listed_first() -> None:
    suggested = make_event("2025mibro", "Goonettes Invitational", "Brownstown", "MI")
    exact = make_event("2024mibro", "Goonettes Invitational", "Brownstown", "MI")
    renamed = make_event(
        "2024mibr2", "Goonettes Invitational - Day 2", "Brownstown", "MI"
    )
    unrelated = make_event("2024miket", "Kettering Kickoff", "Flint", "MI")

    assert SimilarEventHelper.similar_events(
        suggested, [unrelated, renamed, exact]
    ) == [exact, renamed]


def test_same_name_in_another_state_ranks_below_local_match() -> None:
    suggested = make_event("2025txri", "Texas Robotics Invitational", "Houston", "TX")
    local = make_event("2024txri", "Texas Robotics Invitational", "Houston", "TX")
    far_away = make_event(
        "2024mnri", "Minnesota Robotics Invitational", "Minneapolis", "MN"
    )

    assert SimilarEventHelper.similar_events(suggested, [far_away, local])[0] == local


def test_number_of_matches_is_capped() -> None:
    # Multi-stop series (e.g. the Arizona Robotics League) all look alike, but a
    # reviewer only needs to see a handful of them.
    suggested = make_event(
        "2025azrl", "Arizona Robotics League Championship", "Phoenix", "AZ"
    )
    league = [
        make_event(
            f"2024azrl{i}", f"Arizona Robotics League Qualifier {i}", "Phoenix", "AZ"
        )
        for i in range(MAX_SIMILAR_EVENTS + 3)
    ]

    assert len(SimilarEventHelper.similar_events(suggested, league)) == (
        MAX_SIMILAR_EVENTS
    )


def test_limit_and_threshold_are_overridable() -> None:
    suggested = make_event("2025nyny", "Robot Rumble", "Troy", "NY")
    events = [
        make_event("2024nyny", "Robot Rumble", "Troy", "NY"),
        make_event("2024nyt2", "Robot Ruckus", "Troy", "NY"),
    ]

    assert len(SimilarEventHelper.similar_events(suggested, events, limit=1)) == 1
    assert len(SimilarEventHelper.similar_events(suggested, events, threshold=2.0)) == 0


def test_name_similarity_ignores_case_punctuation_and_accents() -> None:
    identical_names = name_similarity("Beach Blitz", "Beach Blitz")
    assert name_similarity("Beach Blitz", "beach-blitz!") == identical_names
    assert (
        name_similarity("Cezeri Robot Ligi Başakşehir", "Cezeri Robot Ligi Basaksehir")
        == identical_names
    )


def test_name_similarity_spells_out_ampersands() -> None:
    identical_names = name_similarity(
        "Robotics and Practical", "Robotics and Practical"
    )
    assert (
        name_similarity("Robotics & Practical", "Robotics and Practical")
        == identical_names
    )


def test_name_similarity_ignores_edition_markers() -> None:
    identical_names = name_similarity("SCRIW", "SCRIW")
    assert name_similarity("SCRIW XI", "SCRIW XIII") == identical_names
    assert (
        name_similarity("Battle of the Bay 2024", "Battle of the Bay")
        == identical_names
    )


def test_name_similarity_of_missing_names() -> None:
    assert name_similarity(None, "Beach Blitz") == 0.0
    assert name_similarity("Beach Blitz", "") == 0.0


def test_name_similarity_of_only_generic_names() -> None:
    # Nothing distinguishing to compare, so these fall back to comparing the
    # names as written rather than comparing two empty strings.
    assert name_similarity("Off-Season Event", "Offseason Event") > SIMILARITY_THRESHOLD
    assert name_similarity("Robotics Competition", "Beach Blitz") < SIMILARITY_THRESHOLD
