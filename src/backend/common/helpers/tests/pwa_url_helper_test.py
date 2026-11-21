import pytest

from backend.common.consts.suggestion_type import SuggestionType
from backend.common.helpers.pwa_url_helper import (
    BETA_BASE_URL,
    LOCAL_PWA_BASE_URL,
    PwaUrlHelper,
)


def test_base_url_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    assert PwaUrlHelper.base_url() == BETA_BASE_URL
    assert PwaUrlHelper.base_url() == "https://beta.thebluealliance.com"


def test_base_url_local_dev_never_points_at_prod(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")
    assert PwaUrlHelper.base_url() == LOCAL_PWA_BASE_URL
    assert "thebluealliance.com" not in PwaUrlHelper.base_url()


def test_base_url_unit_test_defaults_to_beta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAE_ENV", raising=False)
    assert PwaUrlHelper.base_url() == BETA_BASE_URL


def test_suggestion_review_home_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    assert (
        PwaUrlHelper.suggestion_review_url()
        == "https://beta.thebluealliance.com/suggest/review"
    )


@pytest.mark.parametrize(
    "suggestion_type, expected_path",
    [
        (SuggestionType.MATCH, "/suggest/review/match"),
        (SuggestionType.MEDIA, "/suggest/review/media"),
        (SuggestionType.SOCIAL_MEDIA, "/suggest/review/social-media"),
        (SuggestionType.OFFSEASON_EVENT, "/suggest/review/offseason-event"),
        (SuggestionType.API_AUTH_ACCESS, "/suggest/review/api_auth_access"),
        (SuggestionType.ROBOT, "/suggest/review/robot"),
        (SuggestionType.EVENT_MEDIA, "/suggest/review/event_media"),
        (SuggestionType.EVENT, "/suggest/review/event"),
    ],
)
def test_suggestion_review_type_url(
    monkeypatch: pytest.MonkeyPatch,
    suggestion_type: SuggestionType,
    expected_path: str,
) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    assert (
        PwaUrlHelper.suggestion_review_url(suggestion_type)
        == f"https://beta.thebluealliance.com{expected_path}"
    )


def test_suggestion_review_url_local_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")
    assert (
        PwaUrlHelper.suggestion_review_url(SuggestionType.MEDIA)
        == "http://localhost:5173/suggest/review/media"
    )
