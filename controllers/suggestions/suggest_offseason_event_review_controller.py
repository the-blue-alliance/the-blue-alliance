from datetime import datetime
from difflib import SequenceMatcher

from consts.account_permissions import AccountPermissions
from consts.event_type import EventType
from controllers.suggestions.suggestions_review_base_controller import \
    SuggestionsReviewBaseController
from database.event_query import EventListQuery
from helpers.event_manipulator import EventManipulator
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestOffseasonEventReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_OFFSEASON_EVENTS]

    def __init__(self, *args, **kw):
        super(SuggestOffseasonEventReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        event_id = self.request.get("event_short", None)
        event_key = str(self.request.get("year")) + str.lower(str(self.request.get("event_short")))
        if not event_id:
            # Need to supply a key :(
            return 'missing_key', None
        if not Event.validate_key_name(event_key):
            # Bad event key generated
            return 'bad_key', None

        start_date = None
        if self.request.get("start_date"):
            start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")

        end_date = None
        if self.request.get("end_date"):
            end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")

        existing_event = Event.get_by_id(event_key)
        if existing_event:
            return 'duplicate_key', None

        first_code = self.request.get("first_code", '')
        event = Event(
            id=event_key,
            end_date=end_date,
            event_short=self.request.get("event_short"),
            event_type_enum=EventType.OFFSEASON,
            district_key=None,
            venue=self.request.get("venue"),
            venue_address=self.request.get("venue_address"),
            city=self.request.get("city"),
            state_prov=self.request.get("state"),
            country=self.request.get("country"),
            name=self.request.get("name"),
            short_name=self.request.get("short_name"),
            start_date=start_date,
            website=self.request.get("website"),
            year=int(self.request.get("year")),
            first_code=first_code,
            official=(not first_code == ''),
        )
        EventManipulator.createOrUpdate(event)

        author = suggestion.author.get()
        OutgoingNotificationHelper.send_suggestion_result_email(
            to=author.email,
            subject="[TBA] Offseason Event Suggestion: {}".format(event.name),
            email_body="""Dear {},

Thank you for suggesting an offseason event to The Blue Alliance. Your suggestion has been approved and you can find the event at https://www.thebluealliance.com/event/{}

If you are the event's organizer and would like to upload teams attending, match videos, or real-time match results to TBA before or during the event, you can do so using the TBA EventWizard - request auth keys here: https://www.thebluealliance.com/request/apiwrite

Thanks for helping make TBA better,
The Blue Alliance Admins
            """.format(author.nickname, event_key)
        )

        return 'success', event_key

    def was_create_success(self, ret):
        return ret and ret[0] == 'success'

    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "offseason-event")

        year = datetime.now().year
        year_events_future = EventListQuery(year).fetch_async()
        last_year_events_future = EventListQuery(year - 1).fetch_async()
        events_and_ids = [self._create_candidate_event(suggestion) for suggestion in suggestions]

        year_events = year_events_future.get_result()
        year_offseason_events = [e for e in year_events if e.event_type_enum == EventType.OFFSEASON]
        last_year_events = last_year_events_future.get_result()
        last_year_offseason_events = [e for e in last_year_events if e.event_type_enum == EventType.OFFSEASON]

        similar_events = [self._get_similar_events(event[1], year_offseason_events) for event in events_and_ids]
        similar_last_year = [self._get_similar_events(event[1], last_year_offseason_events) for event in events_and_ids]

        self.template_values.update({
            'success': self.request.get("success"),
            'event_key': self.request.get("event_key"),
            'events_and_ids': events_and_ids,
            'similar_events': similar_events,
            'similar_last_year': similar_last_year,
        })
        self.response.out.write(
            jinja2_engine.render('suggestions/suggest_offseason_event_review_list.html', self.template_values))

    def post(self):
        self.verify_permissions()
        id_str = self.request.get("suggestion_id")
        suggestion_id = int(id_str) if id_str.isdigit() else id_str
        verdict = self.request.get("verdict")
        if verdict == "accept":
            status, event_key = self._process_accepted(suggestion_id)
            self.redirect("/suggest/offseason/review?success={}&event_key={}".format(status, event_key))
            return
        elif verdict == "reject":
            self._process_rejected(suggestion_id)
            self.redirect("/suggest/offseason/review?success=reject")
            return

        self.redirect("/suggest/offseason/review")

    @classmethod
    def _create_candidate_event(cls, suggestion):
        start_date = None
        end_date = None
        try:
            start_date = datetime.strptime(suggestion.contents['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(suggestion.contents['end_date'], "%Y-%m-%d")
        except ValueError:
            pass

        venue = suggestion.contents['venue_name']
        address = suggestion.contents['address']
        city = suggestion.contents['city']
        state = suggestion.contents['state']
        country = suggestion.contents['country']
        address = u"{}\n{}\n{}, {}, {}".format(venue, address, city, state, country)
        return suggestion.key.id(), Event(
            end_date=end_date,
            event_type_enum=EventType.OFFSEASON,
            district_key=None,
            venue=venue,
            city=city,
            state_prov=state,
            country=country,
            venue_address=address,
            name=suggestion.contents['name'],
            start_date=start_date,
            website=suggestion.contents['website'],
            year=start_date.year if start_date else None,
            first_code=suggestion.contents.get('first_code', None),
            official=False)

    @classmethod
    def _get_similar_events(cls, candidate_event, offseason_events):
        """
        Finds events this year with a similar name
        Returns a tuple of (event key, event name)
        """
        similar_events = []
        for event in offseason_events:
            similarity = SequenceMatcher(a=candidate_event.name, b=event.name).ratio()
            if similarity > 0.5:
                # Somewhat arbitrary cutoff
                similar_events.append((event.key_name, event.name))
        return similar_events
