import pytest

from backend.common.consts.nexus_match_status import NexusMatchStatus


@pytest.mark.parametrize("status", list(NexusMatchStatus))
def test_round_trip(status: NexusMatchStatus) -> None:
    assert NexusMatchStatus.from_string(status.to_string()) == status


def test_from_string_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown value for NexusMatchStatus"):
        NexusMatchStatus.from_string("Eating lunch")
