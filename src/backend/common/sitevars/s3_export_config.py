from typing import NotRequired, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    aws_access_key: str
    aws_secret_key: str
    s3_bucket_name: str
    export_enabled: bool
    endpoint_url: NotRequired[str]


class S3ExportConfig(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "s3_export_config"

    @staticmethod
    def description() -> str:
        return "Configuration for Parquet export to S3"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            aws_access_key="",
            aws_secret_key="",
            s3_bucket_name="",
            export_enabled=False,
        )

    @classmethod
    def is_enabled(cls) -> bool:
        config = cls.get()
        return bool(
            config.get("export_enabled")
            and config.get("aws_access_key")
            and config.get("aws_secret_key")
            and config.get("s3_bucket_name")
        )
