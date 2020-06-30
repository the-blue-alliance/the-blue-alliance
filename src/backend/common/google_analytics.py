from typing import Optional


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
        event_value: Optional[int] = None,
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

        cid = uuid.uuid3(uuid.NAMESPACE_X500, client_id)

        params = {
            "v": 1,
            "tid": google_analytics_id,
            "cid": str(cid),
            "t": "event",
            "ec": event_category,
            "ea": event_action,
            "ni": 1,
            "sc": "end",  # forces tracking session to end
        }
        if event_value:
            params["ev"] = event_value

        import requests
        requests.get(
            "https://www.google-analytics.com/collect", params=params, timeout=10
        )
