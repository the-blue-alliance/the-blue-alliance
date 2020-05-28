import tba_config

from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_test_creator import SuggestionTestCreator

class AdminCreateTestSuggestions(LoggedInHandler):
    """
    Create test suggestions.
    """
    def get(self):
        self._require_admin()

        if tba_config.CONFIG["env"] != "prod":
            SuggestionTestCreator.createEventWebcastSuggestion()
            SuggestionTestCreator.createMatchVideoSuggestion()
            SuggestionTestCreator.createTeamMediaSuggestion()
        else:
            logging.error("{} tried to create test events in prod! No can do.".format(
                self.user_bundle.user.email()))
        
        self.redirect("/admin/")
