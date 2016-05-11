from consts.account_permissions import AccountPermissions

from controllers.base_controller import LoggedInHandler


class SuggestionsReviewBaseController(LoggedInHandler):
    """
    Base controller for reviewing suggestions.
    """
    def __init__(self, *args, **kw):
        super(SuggestionsReviewBaseController, self).__init__(*args, **kw)
        self._require_permission(AccountPermissions.REVIEW_MEDIA)
