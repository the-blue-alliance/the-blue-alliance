from typing import List, Optional

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class SuggestionQuery(DatabaseQuery[List[Suggestion]]):
    def __init__(
        self,
        review_state: SuggestionState,
        author: Optional[Account] = None,
        reviewer: Optional[Account] = None,
        keys_only: bool = False,
    ) -> None:
        super().__init__(
            review_state=review_state,
            author=author,
            reviewer=reviewer,
            keys_only=keys_only,
        )

    @typed_tasklet
    def _query_async(
        self,
        review_state: SuggestionState,
        author: Optional[Account] = None,
        reviewer: Optional[Account] = None,
        keys_only: bool = False,
    ) -> List[Suggestion]:
        params = [Suggestion.review_state == review_state]
        if author:
            params.append(Suggestion.author == author.key)
        if reviewer:
            params.append(Suggestion.reviewer == reviewer.key)
        return (yield (Suggestion.query(*params).fetch_async(keys_only=keys_only)))
