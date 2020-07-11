from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion
from backend.common.queries.suggestion_query import SuggestionQuery


def test_suggestion() -> None:
    account = Account(id="uid")
    suggestion = Suggestion(author=account.key, target_model=SuggestionType.ROBOT)
    suggestion.put()

    assert [suggestion] == SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING
    ).fetch()
    assert [] == SuggestionQuery(review_state=SuggestionState.REVIEW_ACCEPTED).fetch()


def test_suggestion_author() -> None:
    account = Account(id="uid")
    account.put()

    account_two = Account(id="not")
    account_two.put()

    suggestion = Suggestion(author=account.key, target_model=SuggestionType.ROBOT)
    suggestion.put()

    assert [suggestion] == SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING, author=account
    ).fetch()
    assert (
        []
        == SuggestionQuery(
            review_state=SuggestionState.REVIEW_PENDING, author=account_two
        ).fetch()
    )


def test_suggestion_keys_only() -> None:
    account = Account(id="uid")
    suggestion = Suggestion(author=account.key, target_model=SuggestionType.ROBOT)
    suggestion.put()

    suggestions = SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING, author=account, keys_only=True
    ).fetch()
    assert suggestions == [suggestion.key]


def test_suggestion_reviewer() -> None:
    author = Account(id="author")
    reviewer = Account(id="reviewer")
    suggestion = Suggestion(
        author=author.key, reviewer=reviewer.key, target_model=SuggestionType.ROBOT
    )
    suggestion.put()

    assert [suggestion] == SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING, reviewer=reviewer
    ).fetch()
    assert (
        []
        == SuggestionQuery(
            review_state=SuggestionState.REVIEW_ACCEPTED, reviewer=reviewer
        ).fetch()
    )
    assert (
        []
        == SuggestionQuery(
            review_state=SuggestionState.REVIEW_ACCEPTED, reviewer=author
        ).fetch()
    )


def test_suggestion_reviewer_keys_only() -> None:
    author = Account(id="author")
    reviewer = Account(id="reviewer")
    suggestion = Suggestion(
        author=author.key, reviewer=reviewer.key, target_model=SuggestionType.ROBOT
    )
    suggestion.put()

    suggestions = SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING, reviewer=reviewer, keys_only=True,
    ).fetch()
    assert suggestions == [suggestion.key]


def test_suggestion_author_reviewer() -> None:
    author = Account(id="author")
    author_two = Account(id="author_two")
    reviewer = Account(id="reviewer")
    suggestion = Suggestion(
        author=author.key, reviewer=reviewer.key, target_model=SuggestionType.ROBOT
    )
    suggestion.put()

    assert [suggestion] == SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING, author=author, reviewer=reviewer
    ).fetch()
    assert (
        []
        == SuggestionQuery(
            review_state=SuggestionState.REVIEW_ACCEPTED,
            author=author_two,
            reviewer=reviewer,
        ).fetch()
    )
    assert (
        []
        == SuggestionQuery(
            review_state=SuggestionState.REVIEW_ACCEPTED, author=author, reviewer=author
        ).fetch()
    )


def test_suggestion_author_reviewer_keys_only() -> None:
    author = Account(id="author")
    reviewer = Account(id="reviewer")
    suggestion = Suggestion(
        author=author.key, reviewer=reviewer.key, target_model=SuggestionType.ROBOT
    )
    suggestion.put()

    suggestions = SuggestionQuery(
        review_state=SuggestionState.REVIEW_PENDING,
        author=author,
        reviewer=reviewer,
        keys_only=True,
    ).fetch()
    assert suggestions == [suggestion.key]
