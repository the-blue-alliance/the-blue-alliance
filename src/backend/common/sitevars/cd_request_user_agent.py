from backend.common.sitevars.sitevar import Sitevar


class CdRequestUserAgent(Sitevar[str]):
    @staticmethod
    def key() -> str:
        return "cd.request_user_agent"

    @staticmethod
    def description() -> str:
        return "User-Agent string for Chief Delphi API requests. Required to avoid Cloudflare blocking."

    @staticmethod
    def default_value() -> str:
        return ""

    @classmethod
    def user_agent(cls) -> str:
        return cls.get()
