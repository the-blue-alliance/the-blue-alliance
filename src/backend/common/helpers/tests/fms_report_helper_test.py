from unittest.mock import patch

from backend.common.consts.fms_report_type import FMSReportType
from backend.common.helpers.fms_report_helper import FMSReportHelper

MODULE = "backend.common.helpers.fms_report_helper"


def test_get_existing_reports() -> None:
    with patch(f"{MODULE}.storage_get_files", return_value=["a.xlsx"]) as mock_get:
        assert FMSReportHelper.get_existing_reports("2024test", "qual_rankings") == [
            "a.xlsx"
        ]
    assert mock_get.call_args.kwargs["path"] == FMSReportHelper.get_storage_dir(
        "2024test", FMSReportType.QUAL_RANKINGS
    )


def test_get_existing_reports_storage_error() -> None:
    with patch(f"{MODULE}.storage_get_files", side_effect=Exception("gcs down")):
        assert (
            FMSReportHelper.get_existing_reports(
                "2024test", FMSReportType.QUAL_SCHEDULE
            )
            == []
        )
