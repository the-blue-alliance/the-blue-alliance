import datetime
import logging
from typing import Optional

from flask import Request, Response

from backend.common.auth import current_user
from backend.common.environment import Environment
from backend.common.storage import write as storage_write


class TrustedApiLogger:
    """Helper class for logging Trusted API requests to cloud storage."""

    BUCKET_TEMPLATE = "{project_id}-trustedapi-requests"

    @staticmethod
    def get_bucket() -> str:
        """Get the Trusted API request logging bucket name."""
        project = Environment.project()
        return TrustedApiLogger.BUCKET_TEMPLATE.format(project_id=project)

    @staticmethod
    def should_log_request(request: Request, response: Response) -> bool:
        """Determine if a request should be logged to storage.

        Args:
            request: The Flask request object
            response: The Flask response object

        Returns:
            True if the request should be logged, False otherwise
        """
        # Only log successful requests (2xx status codes)
        if not (200 <= response.status_code < 300):
            return False

        # Only log requests with a body (POST, PATCH, DELETE methods)
        if request.method not in ["POST", "PATCH", "DELETE"]:
            return False

        # Only log if there's a request body
        request_body = request.get_data()
        if not request_body:
            return False

        return True

    @staticmethod
    def log_request(request: Request, response: Response) -> Optional[str]:
        """Log a Trusted API request to cloud storage.

        Args:
            request: The Flask request object
            response: The Flask response object

        Returns:
            The storage path if successful, None if logging failed
        """
        if not TrustedApiLogger.should_log_request(request, response):
            return None

        try:
            # Get request body
            request_body = request.get_data()

            # Prepare storage path
            bucket = TrustedApiLogger.get_bucket()

            # Use URL path as directory
            # For example: /api/trusted/v1/event/2024casj/matches/update/{timestamp}.json
            url_path = request.path.strip("/")
            timestamp = datetime.datetime.now(
                datetime.timezone.utc  # pyre-ignore[16]
            ).isoformat()
            storage_path = f"{url_path}/{timestamp}.json"

            # Prepare metadata
            user = current_user()
            metadata = {
                "X-TBA-Auth-User": str(user.uid) if user else None,
                "X-TBA-Auth-User-Email": user.email if user else None,
                "X-TBA-Auth-Id": request.headers.get("X-TBA-Auth-Id"),
                "method": request.method,
                "status_code": str(response.status_code),
            }

            # Write to storage
            storage_write(
                storage_path,
                request_body,
                bucket=bucket,
                content_type="application/json",
                metadata=metadata,
            )

            logging.info(f"Logged trusted API request to {bucket}/{storage_path}")
            return storage_path

        except Exception as e:
            # Don't fail the request if logging fails
            logging.exception(f"Failed to log trusted API request to storage: {e}")
            return None
