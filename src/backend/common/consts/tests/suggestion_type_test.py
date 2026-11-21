from backend.common.consts.suggestion_type import (
    SuggestionType,
    TYPE_NAMES,
    TYPE_NAMES_SINGULAR,
)


def test_every_type_has_singular_and_plural_names() -> None:
    assert set(TYPE_NAMES) == {t for t in SuggestionType}
    assert set(TYPE_NAMES_SINGULAR) == {t for t in SuggestionType}
