import os
import re

from controllers.base_controller import LoggedInHandler
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion

from template_engine import jinja2_engine


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

        if not match or not event:
            self.abort(404)

        self.template_values.update({
            "status": self.request.get("status"),
            "event": event,
            "match": match,
        })

        self.response.out.write(jinja2_engine.render('suggest_match_video.html', self.template_values))

    def post(self):
        self._require_login()

        match_key = self.request.get("match_key")
        match_future = Match.get_by_id_async(self.request.get("match_key"))
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
            if youtube_id not in match_future.get_result().youtube_videos:
                year = match_key[:4]
                suggestion_id = Suggestion.render_key_name(year, 'match', match_key)
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=self.user_bundle.account.key,
                        target_key=match_key,
                        target_model="match",
                        )
                    suggestion.contents = {"youtube_videos": [youtube_id]}
                    suggestion.put()
                    status = 'success'
                else:
                    status = 'suggestion_exists'
            else:
                status = 'video_exists'
        else:
            status = 'bad_url'

        self.redirect('/suggest/match/video?match_key={}&status={}'.format(match_key, status))
