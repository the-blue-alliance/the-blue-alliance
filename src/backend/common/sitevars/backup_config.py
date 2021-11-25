from typing import List, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    datastore_backup_bucket: str
    datastore_backup_entities: List[str]  # TODO: Can this be typed?
    bigquery_dataset: str


class BackupConfig(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "backup_config"

    @staticmethod
    def description() -> str:
        return "Config for automated backup jobs"

    @staticmethod
    def default_value() -> ContentType:
        # TODO: Should this take a project?
        return ContentType(
            datastore_backup_bucket="tba-prod-rawbackups",
            datastore_backup_entities=[
                "Award",
                "District",
                "DistrictTeam",
                "Event",
                "EventDetails",
                "EventTeam",
                "Match",
                "Team",
            ],
            bigquery_dataset="the_blue_alliance",
        )
