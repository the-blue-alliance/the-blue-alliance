import logging
import os

from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.youtube_video_helper import YouTubeVideoHelper
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion

from template_engine import jinja2_engine


class SuggestMatchVideoController(LoggedInHandler):
    """
    Allow users to suggest videos for TBA to add to matches.
    """

    def get(self):
        self._require_registration()

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

        self.response.out.write(jinja2_engine.render('suggestions/suggest_match_video.html', self.template_values))

    def post(self):
        self._require_registration()

        match_key = self.request.get("match_key")
        youtube_url = self.request.get("youtube_url")
        youtube_id = YouTubeVideoHelper.parse_id_from_url(youtube_url)

        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.user_bundle.account.key, youtube_id, match_key)

        self.redirect('/suggest/match/video?match_key={}&status={}'.format(match_key, status))


class SuggestMatchVideoPlaylistController(LoggedInHandler):
    """
    Allow users to suggest a playlist of YouTube videos for matches
    """
    def get(self):
        self._require_registration()

        if not self.request.get("event_key"):
            self.redirect("/", abort=True)

        event_future = Event.get_by_id_async(self.request.get("event_key"))
        event = event_future.get_result()

        if not event:
            self.abort(404)

        self.template_values.update({
            "event": event,
            "num_added": self.request.get("num_added")
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_match_video_playlist.html', self.template_values))

    def post(self):
        self._require_registration()

        event_key = self.request.get("event_key")
        if not event_key:
            self.response.out.write("No event key found")
            return
        event_future = Event.get_by_id_async(event_key)
        event = event_future.get_result()
        if not event:
            self.response.out.write("Invalid event key {}".format(event_key))
            return

        match_futures = Match.query(Match.event == event.key).fetch_async(keys_only=True)
        valid_match_keys = [match.id() for match in match_futures.get_result()]

        num_videos = int(self.request.get("num_videos", 0))
        suggestions_added = 0
        for i in range(0, num_videos):
            yt_id = self.request.get("video_id_{}".format(i))
            match_partial = self.request.get("match_partial_{}".format(i))
            if not yt_id or not match_partial:
                continue

            match_key = "{}_{}".format(event_key, match_partial)
            if match_key not in valid_match_keys:
                continue

            status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.user_bundle.account.key, yt_id, match_key)
            if status == 'success':
                suggestions_added += 1

        self.redirect('/suggest/event/video?event_key={}&num_added={}'.format(event_key, suggestions_added))
