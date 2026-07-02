from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team


@freeze_time("2025-03-15")
def test_seed_media_suggestions_redirects(local_client: Client, taskqueue_stub) -> None:
    resp = local_client.post("/local/seed_media_suggestions")
    assert resp.status_code == 302
    assert "/suggest/team/media/review" in resp.headers["Location"]


@freeze_time("2025-03-15")
def test_seed_media_suggestions_creates_team(
    local_client: Client, taskqueue_stub
) -> None:
    local_client.post("/local/seed_media_suggestions")

    team = Team.get_by_id("frc2")
    assert team is not None
    assert team.team_number == 2


@freeze_time("2025-03-15")
def test_seed_media_suggestions_creates_account(
    local_client: Client, taskqueue_stub
) -> None:
    local_client.post("/local/seed_media_suggestions")

    account = Account.get_by_id("dev-suggestion-author")
    assert account is not None
    assert account.registered is True


@freeze_time("2025-03-15")
def test_seed_media_suggestions_creates_pending_suggestions(
    local_client: Client, taskqueue_stub
) -> None:
    local_client.post("/local/seed_media_suggestions")

    suggestions = (
        Suggestion.query()
        .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
        .filter(Suggestion.target_model == "media")
        .fetch()
    )
    assert len(suggestions) == 3

    # Verify all have the right target key and author
    account = Account.get_by_id("dev-suggestion-author")
    assert account is not None
    for suggestion in suggestions:
        assert suggestion.contents["reference_key"] == "frc2"
        assert suggestion.author == account.key


@freeze_time("2025-03-15")
def test_seed_media_suggestions_idempotent(
    local_client: Client, taskqueue_stub
) -> None:
    local_client.post("/local/seed_media_suggestions")
    local_client.post("/local/seed_media_suggestions")

    # Second run should not create duplicates
    suggestions = (
        Suggestion.query()
        .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
        .filter(Suggestion.target_model == "media")
        .fetch()
    )
    assert len(suggestions) == 3
