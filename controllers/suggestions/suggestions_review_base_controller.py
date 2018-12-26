import datetime
from google.appengine.ext import ndb

from controllers.base_controller import LoggedInHandler
from models.suggestion import Suggestion
from models.team_admin_access import TeamAdminAccess


class SuggestionsReviewBaseController(LoggedInHandler):
    """
    Base controller for reviewing suggestions.
    """

    REQUIRED_PERMISSIONS = []
    ALLOW_TEAM_ADMIN_ACCESS = False

    def __init__(self, *args, **kw):
        super(SuggestionsReviewBaseController, self).__init__(*args, **kw)
        self.existing_access = []
        if not self.ALLOW_TEAM_ADMIN_ACCESS:
            # For suggestion types that are enabled for delegated mod tools
            # they'll make their own call where they know the team id
            # (verify_permissions only checks the account-level permission)
            self.verify_permissions()

    def verify_write_permissions(self, suggestion):
        # Allow users who have the global permissions
        if all([
                p in self.user_bundle.account.permissions
                for p in self.REQUIRED_PERMISSIONS
        ]):
            return

        # For other team suggestions, make sure the user has a valid access
        if self.ALLOW_TEAM_ADMIN_ACCESS:
            if any([
                    "frc{}".format(a.team_number) == suggestion.target_key
                    for a in self.existing_access
            ]):
                return

        return self.redirect("/", abort=True)

    def verify_permissions(self):
        for permission in self.REQUIRED_PERMISSIONS:
            self._require_permission(permission)

    def get(self):
        self.verify_permissions()

    def post(self):
        self._require_login()
        now = datetime.datetime.now()
        self.existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == self.user_bundle.account.key,
            TeamAdminAccess.expiration > now).fetch()

    def create_target_model(self, suggestion):
        """
        This function creates the model from the accepted suggestion and writes it to the ndb
        """
        raise NotImplementedError(
            "Subclasses should implement create_target_model")

    def was_create_success(self, ret):
        return ret

    @ndb.transactional(xg=True)
    def _process_accepted(self, accept_key):
        """
        Performs all actions for an accepted Suggestion in a Transaction.
        Suggestions are processed one at a time (instead of in batch) in a
        Transaction to prevent possible race conditions.
        """
        # Async get
        suggestion_future = Suggestion.get_by_id_async(accept_key)

        # Resolve async Futures
        suggestion = suggestion_future.get_result()
        self.verify_write_permissions(suggestion)

        # Make sure Suggestion hasn't been processed (by another thread)
        if suggestion.review_state != Suggestion.REVIEW_PENDING:
            return

        # Do all DB writes
        ret = self.create_target_model(suggestion)
        if self.was_create_success(ret):
            # Mark Suggestion as accepted
            suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.datetime.now()
            suggestion.put()
        return ret

    def _process_rejected(self, reject_keys):
        """
        Do everything we need to reject a batch of suggestions
        We can batch these, because we're just rejecting everything
        """
        if not isinstance(reject_keys, list):
            reject_keys = [reject_keys]

        rejected_suggestion_futures = [
            Suggestion.get_by_id_async(key) for key in reject_keys
        ]
        rejected_suggestions = map(lambda a: a.get_result(),
                                   rejected_suggestion_futures)

        for suggestion in rejected_suggestions:
            self.verify_write_permissions(suggestion)
            self._reject_suggestion(suggestion)

    @ndb.transactional(xg=True)
    def _reject_suggestion(self, suggestion):
        if suggestion.review_state == Suggestion.REVIEW_PENDING:
            suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.datetime.now()
            suggestion.put()
