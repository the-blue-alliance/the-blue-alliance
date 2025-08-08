import logging
import uuid

import requests

from backend.common.run_after_response import run_after_response


class GoogleAnalytics:
    """
    Class that manages sending information to Google Analytics 4 (GA4)

    For more information about GA4 Measurement Protocol, visit
    https://developers.google.com/analytics/devguides/collection/protocol/ga4
    """

    @classmethod
    def track_event(
        cls,
        client_id: str,
        event_name: str,
        event_params: dict,
        run_after: bool = False,
    ) -> None:
        from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

        google_analytics_id = GoogleAnalyticsID.google_analytics_id()
        if not google_analytics_id:
            logging.warning(
                "Missing sitevar: google_analytics.id GOOGLE_ANALYTICS_ID. Can't track API usage."
            )
            return

        api_secret = GoogleAnalyticsID.api_secret()
        if not api_secret:
            logging.warning(
                "Missing sitevar: google_analytics.id API_SECRET. Can't track API usage."
            )
            return

        payload = {
            "client_id": str(uuid.uuid3(uuid.NAMESPACE_X500, str(client_id))),
            "events": [
                {
                    "name": event_name,
                    "params": event_params,
                }
            ],
        }

        def make_request():
            requests.post(
                f"https://www.google-analytics.com/mp/collect?measurement_id={google_analytics_id}&api_secret={api_secret}",
                json=payload,
                timeout=10,
            )

        if run_after:
            run_after_response(make_request)
        else:
            make_request()
