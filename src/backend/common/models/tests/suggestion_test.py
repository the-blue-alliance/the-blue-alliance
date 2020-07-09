import json

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion


def test_lazy_load_json() -> None:
    j = {"abc": "def"}
    suggestion = Suggestion(contents_json=json.dumps(j))
    assert suggestion.contents == j


def test_lazy_sets_json() -> None:
    suggestion = Suggestion()
    j = {"abc": "def"}
    suggestion.contents = j
    assert suggestion.contents_json == json.dumps(j)


def test_shadow_banned() -> None:
    account = Account(id="abc", shadow_banned=True)

    suggestion = Suggestion(author=account.put(), target_model=SuggestionType.ROBOT)
    suggestion.put()
    assert suggestion.review_state == SuggestionState.REVIEW_AUTOREJECTED


def test_not_shadow_banned() -> None:
    account = Account(id="abc")

    suggestion = Suggestion(author=account.put(), target_model=SuggestionType.ROBOT)
    suggestion.put()
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
