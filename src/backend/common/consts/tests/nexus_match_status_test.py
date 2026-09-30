import pytest

from backend.common.consts.nexus_match_status import (
    NEXUS_MATCH_STATUS_STRINGS,
    NexusMatchStatus,
)


@pytest.mark.parametrize("status", list(NexusMatchStatus))
def test_round_trip(status: NexusMatchStatus) -> None:
    assert NexusMatchStatus.from_string(status.to_string()) == status


def test_from_string_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown value for NexusMatchStatus"):
        NexusMatchStatus.from_string("Eating lunch")


def test_every_member_has_a_string() -> None:
    assert set(NEXUS_MATCH_STATUS_STRINGS) == set(NexusMatchStatus)
