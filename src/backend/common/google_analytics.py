import time
from typing import Optional

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

        # GA4 requires a different payload structure
        event_params = {
            "event_category": event_category,
            "event_action": event_action,
            "client_id_raw": client_id,  # custom parameter for raw client ID
        }
        if event_label:
            event_params["event_label"] = event_label
        if event_value:
            event_params["event_value"] = event_value

        payload = {
            "client_id": str(cid),
            "events": [
                {
                    "name": f"{event_category}_{event_action}",
                    "params": event_params,
                    "timestamp_micros": int(time.time() * 1000000),
                }
            ],
            "non_personalized_ads": True,  # Equivalent to ni=1 in UA
        }

        def make_request():
            import requests

            requests.post(
                f"https://www.google-analytics.com/mp/collect?measurement_id={google_analytics_id}&api_secret=REPLACE_WITH_API_SECRET",
                json=payload,
                timeout=10,
            )

        if run_after:
            run_after_response(make_request)
        else:
            make_request()
