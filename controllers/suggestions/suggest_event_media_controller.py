from controllers.base_controller import LoggedInHandler
from database.media_query import EventMediasQuery
from helpers.media_helper import MediaHelper
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.event import Event
from template_engine import jinja2_engine


class SuggestEventMediaController(LoggedInHandler):
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

        medias_future = EventMediasQuery(event.key_name).fetch_async()
        medias = medias_future.get_result()
        medias_by_slugname = MediaHelper.group_by_slugname(medias)

        self.template_values.update({
            "status": self.request.get("status"),
            "medias_by_slugname": medias_by_slugname,
            "event": event,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_event_media.html', self.template_values))

    def post(self):
        self._require_registration()

        event_key = self.request.get("event_key")

        status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=self.user_bundle.account.key,
            media_url=self.request.get("media_url"),
            team_key=event_key,
            year_str=event_key[:4])

        self.redirect('/suggest/event/media?event_key=%s&status=%s' % (event_key, status))
