import json
from datetime import datetime

import pytest
from google.cloud import ndb

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
    with pytest.raises(ndb.exceptions.BadValueError):
        Award(
            id="2010ct_1",
            year=2010,
            award_type_enum=1337,
            event_type_enum=EventType.REGIONAL,
            event=ndb.Key(Event, "2010ct"),
            name_str="Winner",
        )


def test_event_type_validation() -> None:
    with pytest.raises(ndb.exceptions.BadValueError):
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
