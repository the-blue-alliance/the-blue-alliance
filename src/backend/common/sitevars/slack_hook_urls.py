from backend.common.sitevars.sitevar import Sitevar


class SlackHookUrls(Sitevar[dict[str, str]]):
    @staticmethod
    def key() -> str:
        return "slack.hookurls"

    @staticmethod
    def description() -> str:
        return "Webhook URLs for Slack Integrations"

    @staticmethod
    def default_value() -> dict[str, str]:
        return {}

    @classmethod
    def url_for(cls, channel: str) -> str | None:
        return cls.get().get(channel)
