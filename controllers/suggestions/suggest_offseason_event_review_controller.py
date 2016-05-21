from datetime import datetime, date

from consts.account_permissions import AccountPermissions
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggestions_review_base_controller import \
    SuggestionsReviewBaseController
from database.event_query import EventListQuery
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestOffseasonEventReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_OFFSEASON_EVENTS)
        super(SuggestOffseasonEventReviewController, self).__init__(*args, **kw)

    def get(self):
        current_year = date.today().year
        all_events_future = EventListQuery(current_year).fetch_async()
        suggestions_future = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "offseason-event").fetch_async()

        existing_offseason_events = filter(lambda e: e.event_type_enum == EventType.OFFSEASON, all_events_future.get_result())
        EventHelper.sort_events(existing_offseason_events)
        events_and_ids = [self._create_candidate_event(suggestion, existing_offseason_events) for suggestion in suggestions_future.get_result()]

        self.template_values.update({
            'success': self.request.get("success"),
            'event_key': self.request.get("event_key"),
            'events_and_ids': events_and_ids,
        })
        self.response.out.write(
            jinja2_engine.render('suggest_offseason_event_review_list.html', self.template_values))

    def post(self):
        self.verify_permissions()
        suggestion = Suggestion.get_by_id(int(self.request.get("suggestion_id")))
        verdict = self.request.get("verdict")
        if verdict == "accept":
            start_date = None
            if self.request.get("start_date"):
                start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")

            end_date = None
            if self.request.get("end_date"):
                end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")

            event = Event(
                id=str(self.request.get("year")) + str.lower(str(self.request.get("event_short"))),
                end_date=end_date,
                event_short=self.request.get("event_short"),
                event_type_enum=EventType.OFFSEASON,
                event_district_enum=DistrictType.NO_DISTRICT,
                venue=self.request.get("venue"),
                venue_address=self.request.get("venue_address"),
                location=self.request.get("location"),
                name=self.request.get("name"),
                short_name=self.request.get("short_name"),
                start_date=start_date,
                website=self.request.get("website"),
                year=int(self.request.get("year")),
                official=False,
            )
            EventManipulator.createOrUpdate(event)

            suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.now()
            suggestion.put()

            self.redirect("/suggest/offseason/review?success=accept&event_key=%s" % event.key.id())
            return
        elif verdict == "reject":
            suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.now()
            suggestion.put()

            self.redirect("/suggest/offseason/review?success=reject")
            return

        self.redirect("/suggest/offseason/review")

    @classmethod
    def _create_candidate_event(cls, suggestion, existing_offseason_events):
        start_date = None
        end_date = None
        try:
            start_date = datetime.strptime(suggestion.contents['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(suggestion.contents['end_date'], "%Y-%m-%d")
        except ValueError:
            pass

        similar_events = filter(lambda x: start_date == x.start_date and end_date == x.end_date, existing_offseason_events)

        return suggestion.key.id(), Event(
            end_date=end_date,
            event_type_enum=EventType.OFFSEASON,
            event_district_enum=DistrictType.NO_DISTRICT,
            venue_address=suggestion.contents['address'],
            name=suggestion.contents['name'],
            start_date=start_date,
            website=suggestion.contents['website'],
            year=start_date.year if start_date else None,
            official=False), similar_events
