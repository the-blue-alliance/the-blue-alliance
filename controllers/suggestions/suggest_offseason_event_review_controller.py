from datetime import datetime

from consts.account_permissions import AccountPermissions
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggestions_review_base_controller import \
    SuggestionsReviewBaseController
from helpers.event_manipulator import EventManipulator
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestOffseasonEventReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_OFFSEASON_EVENTS)
        super(SuggestOffseasonEventReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        event_id = self.request.get("event_short", None)
        event_key = str(self.request.get("year")) + str.lower(str(self.request.get("event_short")))
        if not event_id:
            # Need to supply a key :(
            self.redirect("/suggest/offseason/review?success=missing_key")
            return
        if not Event.validate_key_name(event_key):
            # Bad event key generated
            self.redirect("/suggest/offseason/review?success=bad_key")
            return

        start_date = None
        if self.request.get("start_date"):
            start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")

        end_date = None
        if self.request.get("end_date"):
            end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")

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
            facebook_event=self.request.get("facebook_event"),
            year=int(self.request.get("year")),
            official=False,
        )
        EventManipulator.createOrUpdate(event)
        return event_key

    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "offseason-event")
        events_and_ids = [self._create_candidate_event(suggestion) for suggestion in suggestions]

        self.template_values.update({
            'success': self.request.get("success"),
            'event_key': self.request.get("event_key"),
            'events_and_ids': events_and_ids,
        })
        self.response.out.write(
            jinja2_engine.render('suggestions/suggest_offseason_event_review_list.html', self.template_values))

    def post(self):
        self.verify_permissions()
        suggestion_id = int(self.request.get("suggestion_id"))
        verdict = self.request.get("verdict")
        if verdict == "accept":
            event_key = self._process_accepted(suggestion_id)
            self.redirect("/suggest/offseason/review?success=accept&event_key=%s" % event_key)
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
        address = "{}\n{}\n{}, {}, {}".format(venue, address, city, state, country)
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
            facebook_event=suggestion.contents['facebook_event'],
            year=start_date.year if start_date else None,
            official=False)
