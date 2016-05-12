from consts.account_permissions import AccountPermissions

from controllers.base_controller import LoggedInHandler


class SuggestionsReviewBaseController(LoggedInHandler):
    """
    Base controller for reviewing suggestions.
    """

    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_MEDIA]

    def __init__(self, *args, **kw):
        super(SuggestionsReviewBaseController, self).__init__(*args, **kw)
        self.verify_permissions()

    def verify_permissions(self):
        for permission in self.REQUIRED_PERMISSIONS:
            self._require_permission(permission)
