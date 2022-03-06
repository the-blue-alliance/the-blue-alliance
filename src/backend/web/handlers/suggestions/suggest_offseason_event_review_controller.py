from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Optional, Tuple, Union

from flask import redirect, request
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.suggestion import Suggestion
from backend.common.queries.event_query import EventListQuery
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


@dataclass
class SuggestOffseasonTargetModel:
    status: str
    event_key: Optional[EventKey]


class SuggestOffseasonEventReviewController(
    SuggestionsReviewBase[SuggestOffseasonTargetModel]
):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_OFFSEASON_EVENTS]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def create_target_model(
        self, suggestion: Suggestion
    ) -> Optional[SuggestOffseasonTargetModel]:
        event_id = request.form.get("event_short", None)
        event_key = str(request.form.get("year")) + str.lower(
            str(request.form.get("event_short"))
        )
        if not event_id:
            # Need to supply a key :(
            return SuggestOffseasonTargetModel(status="missing_key", event_key=None)
        if not Event.validate_key_name(event_key):
            # Bad event key generated
            return SuggestOffseasonTargetModel(status="bad_key", event_key=None)

        start_date = None
        if request.form.get("start_date"):
            start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")

        end_date = None
        if request.form.get("end_date"):
            end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")

        existing_event = Event.get_by_id(event_key)
        if existing_event:
            return SuggestOffseasonTargetModel(status="duplicate_key", event_key=None)

        first_code = request.form.get("first_code", "")
        event = Event(
            id=event_key,
            end_date=end_date,
            event_short=request.form.get("event_short"),
            event_type_enum=EventType.OFFSEASON,
            district_key=None,
            venue=request.form.get("venue"),
            venue_address=request.form.get("venue_address"),
            city=request.form.get("city"),
            state_prov=request.form.get("state"),
            country=request.form.get("country"),
            name=request.form.get("name"),
            short_name=request.form.get("short_name"),
            start_date=start_date,
            website=request.form.get("website"),
            year=int(request.form.get("year")),
            first_code=first_code,
            official=(not first_code == ""),
        )
        EventManipulator.createOrUpdate(event)

        """
        author = suggestion.author.get()
        TODO port outoing notifications
        OutgoingNotificationHelper.send_suggestion_result_email(
            to=author.email,
            subject="[TBA] Offseason Event Suggestion: {}".format(event.name),
            email_body="Dear {}, \
\
Thank you for suggesting an offseason event to The Blue Alliance. Your suggestion has been approved and you can find the event at https://www.thebluealliance.com/event/{} \
\
If you are the event's organizer and would like to upload teams attending, match videos, or real-time match results to TBA before or during the event, you can do so using the TBA EventWizard - request auth keys here: https://www.thebluealliance.com/request/apiwrite\
\
Thanks for helping make TBA better,\
The Blue Alliance Admins\
            ".format(author.nickname, event_key)
        )
        """

        return SuggestOffseasonTargetModel(
            status="success",
            event_key=event_key,
        )

    def was_create_success(self, ret: Optional[SuggestOffseasonTargetModel]) -> bool:
        return ret is not None and ret.status == "success"

    def get(self) -> Response:
        super().get()
        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "offseason-event")
        )

        year = datetime.now().year
        year_events_future = EventListQuery(year).fetch_async()
        last_year_events_future = EventListQuery(year - 1).fetch_async()
        events_and_ids = [
            self._create_candidate_event(suggestion) for suggestion in suggestions
        ]

        year_events = year_events_future.get_result()
        year_offseason_events = [
            e for e in year_events if e.event_type_enum == EventType.OFFSEASON
        ]
        last_year_events = last_year_events_future.get_result()
        last_year_offseason_events = [
            e for e in last_year_events if e.event_type_enum == EventType.OFFSEASON
        ]

        similar_events = [
            self._get_similar_events(event[1], year_offseason_events)
            for event in events_and_ids
        ]
        similar_last_year = [
            self._get_similar_events(event[1], last_year_offseason_events)
            for event in events_and_ids
        ]

        template_values = {
            "success": request.args.get("success"),
            "event_key": request.args.get("event_key"),
            "events_and_ids": events_and_ids,
            "similar_events": similar_events,
            "similar_last_year": similar_last_year,
        }
        return render_template(
            "suggestions/suggest_offseason_event_review_list.html", template_values
        )

    def post(self) -> Response:
        super().post()
        self.verify_permissions()

        id_str = request.form.get("suggestion_id")
        suggestion_id = int(id_str) if id_str.isdigit() else id_str
        verdict = request.form.get("verdict")
        if verdict == "accept":
            accepted = self._process_accepted(suggestion_id)
            return redirect(
                "/suggest/offseason/review?success={}&event_key={}".format(
                    accepted.status, accepted.event_key
                )
            )
        elif verdict == "reject":
            self._process_rejected([suggestion_id])
            return redirect("/suggest/offseason/review?success=reject")

        return redirect("/suggest/offseason/review")

    @classmethod
    def _create_candidate_event(
        cls, suggestion: Suggestion
    ) -> Tuple[Union[int, str], Event]:
        start_date = None
        end_date = None
        try:
            start_date = datetime.strptime(
                suggestion.contents["start_date"], "%Y-%m-%d"
            )
            end_date = datetime.strptime(suggestion.contents["end_date"], "%Y-%m-%d")
        except ValueError:
            pass

        venue = suggestion.contents["venue_name"]
        address = suggestion.contents["address"]
        city = suggestion.contents["city"]
        state = suggestion.contents["state"]
        country = suggestion.contents["country"]
        address = "{}\n{}\n{}, {}, {}".format(venue, address, city, state, country)
        return none_throws(suggestion.key.id()), Event(
            end_date=end_date,
            event_type_enum=EventType.OFFSEASON,
            district_key=None,
            venue=venue,
            city=city,
            state_prov=state,
            country=country,
            venue_address=address,
            name=suggestion.contents["name"],
            start_date=start_date,
            website=suggestion.contents["website"],
            year=start_date.year if start_date else None,
            first_code=suggestion.contents.get("first_code", None),
            official=False,
        )

    @classmethod
    def _get_similar_events(
        cls, candidate_event: Event, offseason_events: List[Event]
    ) -> List[Tuple[str, str]]:
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
