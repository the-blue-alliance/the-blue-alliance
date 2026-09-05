from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from flask import redirect, request
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.similar_event_helper import SimilarEventHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
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

    @property
    def _audit_target_kind(self) -> Optional[str]:
        return None

    def create_target_model(
        self, suggestion: Suggestion
    ) -> Optional[SuggestOffseasonTargetModel]:
        year = int(request.form.get("year", 0))
        event_short = request.form.get("event_short", None)
        if event_short:
            event_short = event_short.lower()
        event_key = f"{year}{event_short}"
        if not event_short:
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

        first_code = request.form.get("first_code")
        if first_code:
            first_code = first_code.strip().upper()
        event_type_enum = int(request.form.get("event_type_enum", EventType.OFFSEASON))
        event = Event(
            id=event_key,
            end_date=end_date,
            event_short=event_short,
            event_type_enum=EventType(event_type_enum),
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
            year=year,
            first_code=first_code,
            official=(first_code is not None and first_code != ""),
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

    def _get_accepted_audit_target_key(
        self,
        suggestion: Suggestion,
        ret: Optional[SuggestOffseasonTargetModel],
    ) -> Optional[ndb.Key]:
        if ret and ret.event_key:
            return ndb.Key(Event, ret.event_key)
        return None

    def get(self) -> Response:
        super().get()
        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "offseason-event")
        )

        events_and_ids = [
            self._create_candidate_event(suggestion) for suggestion in suggestions
        ]

        # Compare each suggestion against the year it happens in, not against
        # the year we happen to be reviewing it in -- suggestions for next
        # year's preseason events show up before the new year starts.
        default_year = datetime.now().year
        similar_years = [event.year or default_year for _, event in events_and_ids]

        offseasons_by_year = self._fetch_offseason_events(
            {year for y in similar_years for year in (y, y - 1)}
        )

        similar_events = [
            self._get_similar_events(event, offseasons_by_year.get(year, []))
            for (_, event), year in zip(events_and_ids, similar_years)
        ]
        similar_last_year = [
            self._get_similar_events(event, offseasons_by_year.get(year - 1, []))
            for (_, event), year in zip(events_and_ids, similar_years)
        ]

        template_values = {
            "success": request.args.get("success"),
            "event_key": request.args.get("event_key"),
            "events_and_ids": events_and_ids,
            "similar_events": similar_events,
            "similar_last_year": similar_last_year,
            "similar_years": similar_years,
        }
        return render_template(
            "suggestions/suggest_offseason_event_review_list.html", template_values
        )

    def post(self) -> Response:
        super().post()
        self.verify_permissions()

        id_str = request.form.get("suggestion_id", "")
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
        event_type = suggestion.contents.get("event_type", EventType.OFFSEASON)
        return none_throws(suggestion.key.id()), Event(
            end_date=end_date,
            event_type_enum=event_type or EventType.OFFSEASON,
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
    def _fetch_offseason_events(cls, years: Set[Year]) -> Dict[Year, List[Event]]:
        """
        Fetches the non-official events for each year, keyed by year
        """
        futures = {year: EventListQuery(year).fetch_async() for year in years}
        return {
            year: [e for e in future.get_result() if e.is_offseason]
            for year, future in futures.items()
        }

    @classmethod
    def _get_similar_events(
        cls, candidate_event: Event, offseason_events: List[Event]
    ) -> List[Tuple[str, str]]:
        """
        Finds the events most likely to be the same event as the suggestion,
        best match first.
        Returns a list of (event key, event name)
        """
        return [
            (event.key_name, event.name)
            for event in SimilarEventHelper.similar_events(
                candidate_event, offseason_events
            )
        ]
