from backend.common.consts.award_type import AwardType
from backend.common.models.championship_qualification_method import (
    ChampionshipInviteReason,
    ChampionshipQualificationMethod,
)


def test_invite_reason_values() -> None:
    # These values are persisted in JSON; they must stay stable.
    assert ChampionshipInviteReason.OTHER == 0
    assert ChampionshipInviteReason.PREQUALIFIED == 1
    assert ChampionshipInviteReason.WAITLIST == 2
    assert ChampionshipInviteReason.EVENT_WINNING_ALLIANCE_MEMBER == 3
    assert ChampionshipInviteReason.AWARD_WINNER == 4
    assert ChampionshipInviteReason.POINT_RANKING == 5
    assert ChampionshipInviteReason.WINNING_ALLIANCE_CAPTAIN == 6
    assert ChampionshipInviteReason.WINNING_ALLIANCE_FIRST_PICK == 7
    assert len(ChampionshipInviteReason) == 8


def test_qualification_method_optional_fields() -> None:
    award_method: ChampionshipQualificationMethod = {
        "invite_reason": ChampionshipInviteReason.AWARD_WINNER,
        "event": "2025casj",
        "award": AwardType.CHAIRMANS,
    }
    assert award_method["invite_reason"] == ChampionshipInviteReason.AWARD_WINNER
    assert award_method["event"] == "2025casj"
    assert award_method["award"] == AwardType.CHAIRMANS

    prequalified: ChampionshipQualificationMethod = {
        "invite_reason": ChampionshipInviteReason.PREQUALIFIED,
    }
    assert "event" not in prequalified
    assert "award" not in prequalified
