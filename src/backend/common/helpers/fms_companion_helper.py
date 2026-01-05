import datetime
import logging
from pathlib import Path
from typing import Optional

from backend.common.environment import Environment
from backend.common.models.keys import EventKey
from backend.common.storage import (
    get_files as storage_get_files,
    read as storage_read,
    write as storage_write,
)


class FMSCompanionHelper:
    """Helper class for managing FMS Companion database files in cloud storage."""

    # Constants
    FMS_COMPANION_BUCKET_TEMPLATE = "eventwizard-fms-companion.{project_id}.appspot.com"
    FMS_COMPANION_DIR_TEMPLATE = "fms_companion/{event_key}/"

    @staticmethod
    def get_bucket() -> str:
        project = Environment.project()
        return FMSCompanionHelper.FMS_COMPANION_BUCKET_TEMPLATE.format(
            project_id=project
        )

    @staticmethod
    def get_storage_dir(event_key: EventKey) -> str:
        """Get the storage directory path for an event's FMS companion databases."""
        return FMSCompanionHelper.FMS_COMPANION_DIR_TEMPLATE.format(event_key=event_key)

    @staticmethod
    def get_newest_file_path(event_key: EventKey) -> Optional[str]:
        """
        Get the path to the newest FMS companion database file for an event.

        Args:
            event_key: The event key to get the companion DB for

        Returns:
            The full storage path to the newest file, or None if no files exist
        """
        storage_dir = FMSCompanionHelper.get_storage_dir(event_key)

        try:
            files = storage_get_files(
                path=storage_dir,
                bucket=FMSCompanionHelper.get_bucket(),
            )
            logging.info(f"Found files for event {event_key} in {storage_dir}: {files}")
        except Exception as e:
            logging.error(f"Error listing files from storage: {e}")
            return None

        if not files:
            return None

        # Files are named like: fms_companion.{timestamp}.db
        # Sort by timestamp (embedded in filename) to get the newest
        return sorted(files)[-1]

    @staticmethod
    def read_newest_companion_db(event_key: EventKey) -> Optional[bytes]:
        """
        Read the newest FMS companion database file for an event.

        Args:
            event_key: The event key to get the companion DB for

        Returns:
            The file contents as bytes, or None if no file exists or read fails
        """
        newest_file = FMSCompanionHelper.get_newest_file_path(event_key)
        if not newest_file:
            return None

        try:
            content = storage_read(
                newest_file,
                bucket=FMSCompanionHelper.get_bucket(),
            )
            return content
        except Exception as e:
            logging.exception(f"Error reading file from storage: {e}")
            return None

    @staticmethod
    def write_companion_db(
        event_key: EventKey,
        file_contents: bytes,
        filename: str = "fms_companion.db",
        content_type: str = "application/x-sqlite3",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Write an FMS companion database file to storage.

        Args:
            event_key: The event key to store the companion DB for
            file_contents: The database file contents
            filename: The original filename (used to preserve name and extension)
            content_type: The MIME type of the file
            metadata: Optional metadata to attach to the file

        Returns:
            The full storage path where the file was written
        """
        parsed_filename = Path(filename)
        file_name = parsed_filename.stem
        extension = "".join(parsed_filename.suffixes)

        # Use current timestamp for uniqueness
        timestamp = datetime.datetime.utcnow().isoformat()

        storage_dir = FMSCompanionHelper.get_storage_dir(event_key)
        storage_file = f"{file_name}.{timestamp}{extension}"
        storage_path = f"{storage_dir}/{storage_file}"

        logging.info(f"Writing FMS companion DB to {storage_path}")
        storage_write(
            storage_path,
            file_contents,
            bucket=FMSCompanionHelper.FMS_COMPANION_BUCKET,
            content_type=content_type,
            metadata=metadata or {},
        )

        return storage_path
