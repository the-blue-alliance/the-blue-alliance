import json

from models.sitevar import Sitevar


class GoogleAnalyticsID:

    @staticmethod
    def _default_sitevar():
        return Sitevar.get_or_insert('google_analytics.id', values_json=json.dumps({'GOOGLE_ANALYTICS_ID': ''}))

    @staticmethod
    def google_analytics_id():
        google_analytics_id = GoogleAnalyticsID._default_sitevar()
        return google_analytics_id.contents.get('GOOGLE_ANALYTICS_ID', '')
