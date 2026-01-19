from typing import Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    cloudrun_region: str


class GoogleCloudRunConfig(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "google.cloudrun_config"

    @staticmethod
    def description() -> str:
        return "Configuration for Google Cloud Run"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(cloudrun_region="")

    @classmethod
    def region(cls) -> Optional[str]:
        """Get the configured Cloud Run region.

        Returns:
            The Cloud Run region, or None if not configured.
        """
        region = cls.get().get("cloudrun_region")
        return region if region else None  # Drop empty strings
