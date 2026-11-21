from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_details import EventDetails
from backend.common.queries.dict_converters.event_details_converter import (
    EventDetailsConverter,
)


def test_eventDetailsConverter_v3_empty_details(ndb_context) -> None:
    details = EventDetails(id="2019nyny")
    converted = EventDetailsConverter.eventDetailsConverter_v3(details)
    assert converted == {
        "alliances": None,
        "district_points": None,
        "regional_champs_pool_points": None,
        "insights": None,
        "oprs": {},
        "predictions": None,
        "rankings": details.renderable_rankings,
        "coprs": {},
    }
    assert converted["rankings"]["rankings"] == []


def test_eventDetailsConverter_v3_normalizes_stat_team_keys(ndb_context) -> None:
    details = EventDetails(
        id="2019nyny",
        matchstats={
            "oprs": {"frc254": 10.0, "1114": 20.0},
            "dprs": {"frc254": 1.0},
            "ccwms": {"1114": 2.0},
            # Only oprs/dprs/ccwms are passed through
            "unknown": {"frc254": 99.0},
        },
        coprs={
            "Total Points": {"frc254": 5.0, "1114": 6.0},
        },
    )

    converted = EventDetailsConverter.eventDetailsConverter_v3(details)

    assert converted["oprs"] == {
        "oprs": {"frc254": 10.0, "frc1114": 20.0},
        "dprs": {"frc254": 1.0},
        "ccwms": {"frc1114": 2.0},
    }
    assert converted["coprs"] == {"Total Points": {"frc254": 5.0, "frc1114": 6.0}}


def test_eventDetailsConverter_v3_none_details(ndb_context) -> None:
    # The converter tolerates a missing EventDetails by rendering empty fields
    converted = EventDetailsConverter.eventDetailsConverter_v3(None)  # pyre-ignore[6]
    assert converted == {
        "alliances": [],
        "district_points": {},
        "regional_champs_pool_points": {},
        "insights": {"qual": {}, "playoff": {}},
        "oprs": {},
        "predictions": {},
        "rankings": {
            "extra_stats_info": [],
            "rankings": [],
            "sort_order_info": None,
        },
        "coprs": {},
    }


def test_convert(ndb_context) -> None:
    details = EventDetails(id="2019nyny")
    converted = EventDetailsConverter(details).convert(ApiMajorVersion.API_V3)
    assert converted == EventDetailsConverter.eventDetailsConverter_v3(details)
