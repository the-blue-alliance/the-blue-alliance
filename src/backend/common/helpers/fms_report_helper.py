import datetime
import logging
from pathlib import Path
from typing import cast, Optional, Union

from backend.common.consts.fms_report_type import FMSReportType
from backend.common.environment import Environment
from backend.common.models.keys import EventKey
from backend.common.storage import (
    get_files as storage_get_files,
    write as storage_write,
)


class FMSReportHelper:
    """Helper class for managing FMS report files in cloud storage."""

    # Constants
    FMS_REPORT_BUCKET_TEMPLATE = "{project_id}-eventwizard-fms-reports"
    FMS_REPORT_DIR_TEMPLATE = "fms_reports/{event_key}/{report_type}/"

    @staticmethod
    def get_bucket() -> str:
        """Get the FMS report bucket name based on the current environment."""
        project = Environment.project()
        return FMSReportHelper.FMS_REPORT_BUCKET_TEMPLATE.format(project_id=project)

    @staticmethod
    def get_storage_dir(event_key: EventKey, report_type: FMSReportType) -> str:
        """Get the storage directory path for an event's FMS reports of a given type.

        Args:
            event_key: The event key to get the reports for
            report_type: The type of report

        Returns:
            The storage directory path
        """
        return FMSReportHelper.FMS_REPORT_DIR_TEMPLATE.format(
            event_key=event_key, report_type=report_type.value
        )

    @staticmethod
    def get_existing_reports(
        event_key: EventKey, report_type: Union[str, FMSReportType]
    ) -> list[str]:
        """Get a list of existing FMS report files for an event and report type.

        Args:
            event_key: The event key to get the reports for
            report_type: The type of report (str or FMSReportType enum)

        Returns:
            A list of file paths in storage
        """
        report_type_enum = (
            FMSReportType(report_type) if isinstance(report_type, str) else report_type
        )
        storage_dir = FMSReportHelper.get_storage_dir(
            event_key, cast(FMSReportType, report_type_enum)
        )

        try:
            files = storage_get_files(
                path=storage_dir,
                bucket=FMSReportHelper.get_bucket(),
            )
            logging.info(
                f"Found {len(files)} report files for event {event_key}, "
                f"type {report_type} in {storage_dir}"
            )
            return files
        except Exception as e:
            logging.error(f"Error listing files from storage: {e}")
            return []

    @staticmethod
    def write_report(
        event_key: EventKey,
        report_type: Union[str, FMSReportType],
        file_contents: bytes,
        filename: str,
        mtime: datetime.datetime,
        content_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        metadata: Optional[dict] = None,
    ) -> tuple[str, bool]:
        """Write an FMS report file to storage if it doesn't already exist.

        Args:
            event_key: The event key to store the report for
            report_type: The type of report (str or FMSReportType enum)
            file_contents: The report file contents
            filename: The original filename
            mtime: The modification time from the Excel file
            content_type: The MIME type of the file
            metadata: Optional metadata to attach to the file

        Returns:
            A tuple of (storage_path, was_written) where was_written indicates
            if the file was newly written (True) or already existed (False)
        """
        parsed_filename = Path(filename)
        file_name = parsed_filename.stem
        extension = "".join(parsed_filename.suffixes)

        report_type_enum = (
            FMSReportType(report_type) if isinstance(report_type, str) else report_type
        )
        storage_dir = FMSReportHelper.get_storage_dir(
            event_key, cast(FMSReportType, report_type_enum)
        )
        storage_file = f"{file_name}.{mtime}{extension}"
        storage_path = f"{storage_dir}/{storage_file}"

        # Check if file already exists
        existing_reports = FMSReportHelper.get_existing_reports(event_key, report_type)
        if any(
            existing.split("/")[-1] == storage_file for existing in existing_reports
        ):
            logging.info(
                f"Report file already exists at {storage_path}, skipping write"
            )
            return storage_path, False

        logging.info(f"Writing FMS report to {storage_path}")
        storage_write(
            storage_path,
            file_contents,
            bucket=FMSReportHelper.get_bucket(),
            content_type=content_type,
            metadata=metadata or {},
        )

        return storage_path, True
