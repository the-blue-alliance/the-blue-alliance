import json
from datetime import datetime

import pytest
from google.appengine.api import datastore_errors
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.event import Event


@pytest.mark.parametrize("key", ["2010ct_3", "2010ct2_12"])
def test_valid_key_names(key: str) -> None:
    assert Award.validate_key_name(key) is True


@pytest.mark.parametrize(
    "key", ["2010ct", "2010ct_frc177", "2010ct_asadf", "2010ct_-1"]
)
def test_invalid_key_names(key: str) -> None:
    assert Award.validate_key_name(key) is False


def test_key_name() -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
    )

    assert a.key_name == "2010ct_1"


def test_award_type_validation() -> None:
    with pytest.raises(datastore_errors.BadValueError):
        Award(
            id="2010ct_1",
            year=2010,
            award_type_enum=1337,
            event_type_enum=EventType.REGIONAL,
            event=ndb.Key(Event, "2010ct"),
            name_str="Winner",
        )


def test_event_type_validation() -> None:
    with pytest.raises(datastore_errors.BadValueError):
        Award(
            id="2010ct_1",
            year=2010,
            award_type_enum=AwardType.WINNER,
            event_type_enum=1337,
            event=ndb.Key(Event, "2010ct"),
            name_str="Winner",
        )


def test_blue_banners() -> None:
    a1 = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
    )

    assert a1.is_blue_banner is True
    assert a1.count_banner is True

    a2 = Award(
        id="2010ct_66",
        year=2010,
        award_type_enum=AwardType.GOLDEN_CORNDOG,
        event_type_enum=EventType.OFFSEASON,
        event=ndb.Key(Event, "2010ct"),
        name_str="Golden Corndog",
    )

    assert a2.is_blue_banner is False
    assert a2.count_banner is True


def test_check_wfa_cmp_banner_2champs() -> None:
    Event(
        id="2017cmp1",
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime(2017, 3, 1),
        year=2017,
        event_short="cmp1",
    ).put()
    Event(
        id="2017cmp2",
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime(2017, 3, 2),
        year=2017,
        event_short="cmp2",
    ).put()

    a1 = Award(
        id="2017cmp1_3",
        year=2017,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.CMP_FINALS,
        event=ndb.Key(Event, "2017cmp1"),
        name_str="WFA",
    )
    a2 = Award(
        id="2017cmp2_3",
        year=2017,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.CMP_FINALS,
        event=ndb.Key(Event, "2017cmp2"),
        name_str="WFA",
    )

    assert a1.count_banner is True
    assert a2.count_banner is False


def test_normalized_name() -> None:
    a1 = Award(
        id="2010ct_66",
        year=2010,
        award_type_enum=AwardType.GOLDEN_CORNDOG,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Golden Corndog",
    )
    assert a1.normalized_name == "Golden Corndog"

    a2 = Award(
        id="2010ct_3",
        year=2010,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="WFFA",
    )
    assert a2.normalized_name == "Woodie Flowers Finalist Award"

    a3 = Award(
        id="2010ct_3",
        year=2010,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.CMP_FINALS,
        event=ndb.Key(Event, "2010ct"),
        name_str="WFFA",
    )
    assert a3.normalized_name == "Woodie Flowers Award"


def test_normalized_name_chairmans_impact() -> None:
    # Before 2023, should be Chairman's Award
    a1 = Award(
        id="2022ct_0",
        year=2022,
        award_type_enum=AwardType.CHAIRMANS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2022ct"),
        name_str="Regional Chairman's Award",
    )
    assert a1.normalized_name == "Chairman's Award"

    # 2023 and later, should be FIRST Impact Award
    a2 = Award(
        id="2023ct_0",
        year=2023,
        award_type_enum=AwardType.CHAIRMANS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2023ct"),
        name_str="Regional FIRST Impact Award",
    )
    assert a2.normalized_name == "FIRST Impact Award"


def test_normalized_name_deans_list_leadership() -> None:
    # Before 2026, should be Dean's List (falls through to name_str)
    a1 = Award(
        id="2025ct_4",
        year=2025,
        award_type_enum=AwardType.DEANS_LIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2025ct"),
        name_str="FIRST Dean's List Finalist Award",
    )
    assert a1.normalized_name == "FIRST Dean's List Finalist Award"

    # 2026 and later, should be FIRST Leadership Award
    a2 = Award(
        id="2026ct_4",
        year=2026,
        award_type_enum=AwardType.DEANS_LIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2026ct"),
        name_str="FIRST Leadership Award",
    )
    assert a2.normalized_name == "FIRST Leadership Award"


def test_recipients_team() -> None:
    recipients = [AwardRecipient(awardee=None, team_number=176)]
    a1 = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
        recipient_json_list=[json.dumps(r) for r in recipients],
    )
    assert a1.recipient_list == recipients
    assert a1.recipient_list_json == json.dumps(recipients)

    recipient_dict = a1.recipient_dict
    assert 176 in recipient_dict
    assert recipient_dict[176] == [None]


def test_recipients_individual() -> None:
    recipients = [AwardRecipient(awardee="Woodie Flowers", team_number=None)]
    a1 = Award(
        id="2010ct_3",
        year=2010,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="WFFA",
        recipient_json_list=[json.dumps(r) for r in recipients],
    )
    assert a1.recipient_list == recipients
    assert a1.recipient_list_json == json.dumps(recipients)

    recipient_dict = a1.recipient_dict
    assert None in recipient_dict
    assert recipient_dict[None] == ["Woodie Flowers"]
