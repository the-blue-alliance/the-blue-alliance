from typing import Dict, Optional

from backend.common.sitevars.sitevar import Sitevar


class SlackHookUrls(Sitevar[Dict[str, str]]):
    @staticmethod
    def key() -> str:
        return "slack.hookurls"

    @staticmethod
    def description() -> str:
        return "Webhook URLs for Slack Integrations"

    @staticmethod
    def default_value() -> Dict[str, str]:
        return {}

    @classmethod
    def url_for(cls, channel: str) -> Optional[str]:
        return cls.get().get(channel)
