from backend.common.consts.suggestion_state import SuggestionState
from backend.common.futures import TypedFuture
from backend.common.models.suggestion import Suggestion


class SuggestionFetcher:
    @staticmethod
    def count_async(
        review_state: SuggestionState, suggestion_type: str
    ) -> TypedFuture[int]:
        return (
            Suggestion.query()
            .filter(Suggestion.review_state == review_state)
            .filter(Suggestion.target_model == suggestion_type)
            .count_async()
        )
