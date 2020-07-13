import pytest

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess


def test_read_type_put() -> None:
    auth = ApiAuthAccess(auth_types_enum=[AuthType.EVENT_INFO, AuthType.READ_API])

    with pytest.raises(
        Exception, match="Cannot combine AuthType.READ_API with other write auth types"
    ):
        auth.put()

    auth.auth_types_enum = [AuthType.EVENT_INFO]
    auth.put()

    auth.auth_types_enum = [AuthType.READ_API]
    auth.put()


def test_can_edit_event_info() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_info
    auth.auth_types_enum = [AuthType.EVENT_INFO]
    assert auth.can_edit_event_info


def test_can_edit_event_teams() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_teams
    auth.auth_types_enum = [AuthType.EVENT_TEAMS]
    assert auth.can_edit_event_teams


def test_can_edit_event_matches() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_matches
    auth.auth_types_enum = [AuthType.EVENT_MATCHES]
    assert auth.can_edit_event_matches


def test_can_edit_event_rankings() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_rankings
    auth.auth_types_enum = [AuthType.EVENT_RANKINGS]
    assert auth.can_edit_event_rankings


def test_can_edit_event_alliances() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_alliances
    auth.auth_types_enum = [AuthType.EVENT_ALLIANCES]
    assert auth.can_edit_event_alliances


def test_can_edit_event_awards() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_event_awards
    auth.auth_types_enum = [AuthType.EVENT_AWARDS]
    assert auth.can_edit_event_awards


def test_can_edit_match_video() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_match_video
    auth.auth_types_enum = [AuthType.MATCH_VIDEO]
    assert auth.can_edit_match_video


def test_can_edit_zebra_motionworks() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.can_edit_zebra_motionworks
    auth.auth_types_enum = [AuthType.ZEBRA_MOTIONWORKS]
    assert auth.can_edit_zebra_motionworks


def test_is_read_key() -> None:
    auth = ApiAuthAccess(auth_types_enum=[])
    assert not auth.is_read_key
    auth.auth_types_enum = [AuthType.READ_API]
    assert auth.is_read_key
    auth.auth_types_enum = [
        AuthType.READ_API,
        AuthType.ZEBRA_MOTIONWORKS,
    ]  # Should not happen - but testing just in case
    assert not auth.is_read_key


def test_is_write_key() -> None:
    auth = ApiAuthAccess(auth_types_enum=[AuthType.READ_API])
    assert not auth.is_write_key
    auth.auth_types_enum = []
    assert auth.is_write_key
    auth.auth_types_enum = [AuthType.ZEBRA_MOTIONWORKS]
    assert auth.is_write_key
