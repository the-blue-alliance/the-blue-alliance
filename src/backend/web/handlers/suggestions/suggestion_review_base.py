import datetime
from typing import Generic, List, Optional, TypeVar, Union

from flask import redirect, request, url_for
from flask.views import MethodView
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.exceptions import abort, HTTPException
from werkzeug.wrappers import Response

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.suggestion import Suggestion

# from backend.common.models.team_admin_access import TeamAdminAccess


TTargetModel = TypeVar("TTargetModel")


class SuggestionsReviewBase(Generic[TTargetModel], MethodView):
    """
    Base controller for reviewing suggestions.
    """

    REQUIRED_PERMISSIONS = []
    ALLOW_TEAM_ADMIN_ACCESS = False

    def __init__(self, *args, **kw) -> None:
        super(SuggestionsReviewBase, self).__init__(*args, **kw)
        # TODO port over TeamAdminAccess
        self.existing_access = []
        if not self.ALLOW_TEAM_ADMIN_ACCESS:
            # For suggestion types that are enabled for delegated mod tools
            # they'll make their own call where they know the team id
            # (verify_permissions only checks the account-level permission)
            self.verify_permissions()

    def verify_write_permissions(self, suggestion: Suggestion) -> None:
        # Allow users who have the global permissions
        user = current_user()
        if not user:
            raise HTTPException(
                response=redirect(url_for("account.login", next=request.url))
            )
        if all(
            [
                p in (none_throws(user).permissions or [])
                for p in self.REQUIRED_PERMISSIONS
            ]
        ):
            return

        # For other team suggestions, make sure the user has a valid access
        if self.ALLOW_TEAM_ADMIN_ACCESS:
            if any(
                [
                    "frc{}".format(a.team_number) == suggestion.target_key
                    for a in self.existing_access
                ]
            ):
                return

        abort(401)

    def verify_permissions(self) -> None:
        user = current_user()
        if not user:
            raise HTTPException(
                response=redirect(url_for("account.login", next=request.url))
            )
        user_permissions: List[AccountPermission] = none_throws(user).permissions or []
        for permission in self.REQUIRED_PERMISSIONS:
            if permission not in user_permissions:
                abort(401)

    def get(self) -> Optional[Response]:
        return self.verify_permissions()

    def post(self) -> Optional[Response]:
        """
        now = datetime.datetime.now()
        self.existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == self.user_bundle.account.key,
            TeamAdminAccess.expiration > now).fetch()
        """

    def create_target_model(self, suggestion: Suggestion) -> Optional[TTargetModel]:
        """
        This function creates the model from the accepted suggestion and writes it to the ndb
        """
        raise NotImplementedError

    def was_create_success(self, ret: Optional[TTargetModel]) -> bool:
        return ret is not None

    @ndb.transactional(xg=True)
    def _process_accepted(self, accept_key: str) -> Optional[TTargetModel]:
        """
        Performs all actions for an accepted Suggestion in a Transaction.
        Suggestions are processed one at a time (instead of in batch) in a
        Transaction to prevent possible race conditions.
        """
        # Async get
        suggestion_future = Suggestion.get_by_id_async(accept_key)

        # Resolve async Futures
        suggestion = none_throws(suggestion_future.get_result())
        self.verify_write_permissions(suggestion)

        # Make sure Suggestion hasn't been processed (by another thread)
        if suggestion.review_state != SuggestionState.REVIEW_PENDING:
            return None

        # Do all DB writes
        user = none_throws(current_user())
        ret = self.create_target_model(suggestion)
        if self.was_create_success(ret):
            # Mark Suggestion as accepted
            suggestion.review_state = SuggestionState.REVIEW_ACCEPTED
            suggestion.reviewer = user.account_key
            suggestion.reviewed_at = datetime.datetime.now()
            suggestion.put()
        return ret

    def _process_rejected(self, reject_keys: List[Union[int, str]]) -> None:
        """
        Do everything we need to reject a batch of suggestions
        We can batch these, because we're just rejecting everything
        """
        rejected_suggestion_futures = [
            Suggestion.get_by_id_async(key) for key in reject_keys
        ]
        rejected_suggestions = map(
            lambda a: none_throws(a.get_result()), rejected_suggestion_futures
        )

        for suggestion in rejected_suggestions:
            self.verify_write_permissions(suggestion)
            self._reject_suggestion(suggestion)

    @ndb.transactional(xg=True)
    def _reject_suggestion(self, suggestion: Suggestion) -> None:
        user = none_throws(current_user())
        if suggestion.review_state == SuggestionState.REVIEW_PENDING:
            suggestion.review_state = SuggestionState.REVIEW_REJECTED
            suggestion.reviewer = user.account_key
            suggestion.reviewed_at = datetime.datetime.now()
            suggestion.put()
