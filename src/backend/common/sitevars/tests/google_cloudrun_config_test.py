from backend.common.sitevars.google_cloudrun_config import (
    ContentType,
    GoogleCloudRunConfig,
)


def test_key() -> None:
    assert GoogleCloudRunConfig.key() == "google.cloudrun_config"


def test_description() -> None:
    assert GoogleCloudRunConfig.description() == "Configuration for Google Cloud Run"


def test_default_sitevar() -> None:
    default_sitevar = GoogleCloudRunConfig._fetch_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents == {"cloudrun_region": ""}


def test_region_empty() -> None:
    assert GoogleCloudRunConfig.region() is None


def test_region() -> None:
    GoogleCloudRunConfig.put(ContentType(cloudrun_region="us-central1"))
    assert GoogleCloudRunConfig.region() == "us-central1"
