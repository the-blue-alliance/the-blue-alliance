from typing import Optional

from backend.common.run_after_response import run_after_response


class GoogleAnalytics:
    """
    Class that manages sending information to Google Analytics

    For more information about GAnalytics Protocol Parameters, visit
    https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    """

    @classmethod
    def track_event(
        cls,
        client_id: str,
        event_category: str,
        event_action: str,
        event_label: Optional[str] = None,
        event_value: Optional[int] = None,
        run_after: bool = False,
    ) -> None:
        from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

        google_analytics_id = GoogleAnalyticsID.google_analytics_id()

        if not google_analytics_id:
            import logging

            logging.warning(
                "Missing sitevar: google_analytics.id. Can't track API usage."
            )
            return

        import uuid

        cid = uuid.uuid3(uuid.NAMESPACE_X500, str(client_id))

        params = {
            "v": 1,
            "tid": google_analytics_id,
            "cid": str(cid),
            "t": "event",
            "ec": event_category,
            "ea": event_action,
            "cd1": client_id,  # custom dimension 1 is the raw client ID
            "ni": 1,
            "sc": "end",  # forces tracking session to end
        }
        if event_label:
            params["el"] = event_label
        if event_value:
            params["ev"] = event_value

        def make_request():
            import requests

            requests.get(
                "https://www.google-analytics.com/collect", params=params, timeout=10
            )

        if run_after:
            run_after_response(make_request)
        else:
            make_request()
