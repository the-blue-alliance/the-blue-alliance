import os
import re

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion

class SuggestMatchVideoController(LoggedInHandler):
    """
    Allow users to suggest videos for TBA to add to matches.
    """

    def get(self):
        self._require_login("/suggest/match/video?match=%s" % self.request.get("match_key"))

        if not self.request.get("match_key"):
            self.redirect("/", abort=True)

        match_future = Match.get_by_id_async(self.request.get("match_key"))
        event_future = Event.get_by_id_async(self.request.get("match_key").split("_")[0])
        match = match_future.get_result()
        event = event_future.get_result()

        self.template_values.update({
            "success": self.request.get("success"),
            "event": event,
            "match": match,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_match_video.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login()

        match_key = self.request.get("match_key")
        youtube_url = self.request.get("youtube_url")

        youtube_id = None
        regex1 = re.match(r".*youtu\.be\/(.*)", youtube_url)
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", youtube_url)
            if regex2 is not None:
                youtube_id = regex2.group(1)

        if youtube_id is not None:
            suggestion = Suggestion(
                author = self.user_bundle.account.key,
                target_key = match_key,
                target_model = "match",
                )
            suggestion.contents = {"youtube_videos": [youtube_id]}
            suggestion.put()

        self.redirect('/suggest/match/video?match_key=%s&success=1' % match_key)
