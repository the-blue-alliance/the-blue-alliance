from unittest.mock import Mock, patch

import bs4
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_api_history_not_logged_in(web_client: Client) -> None:
    """Test that unauthenticated users can't access api_history"""
    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 401


def test_api_history_not_admin(web_client: Client, login_gae_user) -> None:
    """Test that non-admin users can't access api_history"""
    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 401


def test_api_history_event_not_found(web_client: Client, login_gae_admin) -> None:
    """Test that 404 is returned when event doesn't exist"""
    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 404


@patch("backend.web.handlers.admin.api_history.Environment.project")
@patch("backend.web.handlers.admin.api_history.Environment.is_dev")
@patch("backend.web.handlers.admin.api_history.get_files")
def test_api_history_with_files(
    mock_get_files: Mock,
    mock_is_dev: Mock,
    mock_project: Mock,
    web_client: Client,
    login_gae_admin,
) -> None:
    """Test that api_history displays FRC API files correctly in production"""
    helpers.preseed_event("2020nyny")
    mock_is_dev.return_value = False
    mock_project.return_value = "testbed-test"

    # Mock cloud storage responses - return different files for different paths
    def mock_get_files_side_effect(*args, **kwargs):
        path = args[0] if args else kwargs.get("path", "")
        bucket = kwargs.get("bucket", None)

        # Check FMS Reports bucket first (most specific)
        if bucket == "testbed-test-eventwizard-fms-reports":
            if "team_list" in path:
                return [
                    "fms_reports/2020nyny/team_list/team_list.2020-03-14T08:00:00.xlsx",
                ]
            elif "qual_schedule" in path:
                return [
                    "fms_reports/2020nyny/qual_schedule/qual_schedule.2020-03-15T09:00:00.xlsx",
                ]
            else:
                return []

        # Check FMS Companion bucket
        if bucket == "testbed-test-eventwizard-fms-companion":
            if "fms_companion" in path:
                return [
                    "fms_companion/2020nyny/fms_companion.2020-03-15T14:30:00.db",
                    "fms_companion/2020nyny/fms_companion.2020-03-14T09:15:00.db",
                ]
            else:
                return []

        # FRC API paths (no bucket or default bucket)
        if "alliances" in path:
            return [
                "frc-api-response/v3.0/2020/alliances/nyny/2020-03-15 10:30:00.json",
                "frc-api-response/v3.0/2020/alliances/nyny/2020-03-15 12:45:00.json",
            ]
        elif "events?eventCode" in path:
            return [
                "frc-api-response/v3.0/2020/events?eventCode=nyny/2020-03-14 08:00:00.json",
            ]
        elif "schedule" in path and "qual" in path:
            return [
                "frc-api-response/v3.0/2020/schedule/nyny/qual/hybrid/2020-03-15 09:00:00.json",
            ]
        else:
            return []

    mock_get_files.side_effect = mock_get_files_side_effect

    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["API History - 2020nyny - TBA Admin"]

    content = resp.data.decode("utf-8")

    # Check that FRC API section headers are present
    assert "Event Details" in content
    assert "Alliance Selection" in content
    assert "Hybrid Schedule - Qualification" in content
    assert "Hybrid Schedule - Playoff" in content
    assert "Match Scores - Qualification" in content
    assert "Match Scores - Playoff" in content
    assert "Event Awards" in content

    # Check that FMS Reports section headers are present
    assert "Team List" in content
    assert "Qualification Schedule" in content
    assert "Playoff Schedule" in content
    assert "Qualification Results" in content
    assert "Playoff Results" in content
    assert "Qualification Rankings" in content
    assert "Playoff Alliances" in content

    # Check that Companion DB section header is present
    assert "FMS Companion Database" in content

    # Check that timestamps are displayed for alliance files
    assert "2020-03-15 12:45:00" in content
    assert "2020-03-15 10:30:00" in content

    # Check that FMS report timestamps are displayed
    assert "2020-03-14T08:00:00" in content
    assert "2020-03-15T09:00:00" in content

    # Check that Companion DB timestamps are displayed
    assert "2020-03-15T14:30:00" in content
    assert "2020-03-14T09:15:00" in content

    # Check that production GCS URLs are present
    assert (
        "https://storage.googleapis.com/testbed-test.appspot.com/frc-api-response/v3.0/2020/alliances/nyny/2020-03-15 12:45:00.json"
        in content
    )
    assert (
        "https://storage.googleapis.com/testbed-test-eventwizard-fms-reports/fms_reports/2020nyny/team_list/team_list.2020-03-14T08:00:00.xlsx"
        in content
    )
    assert (
        "https://storage.googleapis.com/testbed-test-eventwizard-fms-companion/fms_companion/2020nyny/fms_companion.2020-03-15T14:30:00.db"
        in content
    )

    # Verify get_files was called multiple times for different endpoints
    # 7 FRC API endpoints + 7 FMS Reports + 1 Companion DB = 15
    assert mock_get_files.call_count == 15


@patch("backend.web.handlers.admin.api_history.Environment.project")
@patch("backend.web.handlers.admin.api_history.Environment.is_dev")
@patch("backend.web.handlers.admin.api_history.get_files")
def test_api_history_with_files_dev_server(
    mock_get_files: Mock,
    mock_is_dev: Mock,
    mock_project: Mock,
    web_client: Client,
    login_gae_admin,
) -> None:
    """Test that api_history displays dev blobstore URLs in development mode"""
    helpers.preseed_event("2020nyny")
    mock_is_dev.return_value = True
    mock_project.return_value = "testbed-test"

    # Mock cloud storage responses - just return files for one endpoint
    def mock_get_files_side_effect(*args, **kwargs):
        path = args[0] if args else kwargs.get("path", "")
        if "alliances" in path:
            return [
                "frc-api-response/v3.0/2020/alliances/nyny/2020-03-15 10:30:00.json",
            ]
        return []

    mock_get_files.side_effect = mock_get_files_side_effect

    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 200

    content = resp.data.decode("utf-8")

    # Check that section headers are present
    assert "Alliance Selection" in content

    # Check that timestamps are displayed
    assert "2020-03-15 10:30:00" in content

    # Check that dev blobstore URLs are present (not production GCS URLs)
    assert "http://localhost:8000/blobstore/blob/" in content
    assert "display=inline" in content
    # Production URLs should NOT be present
    assert "https://storage.googleapis.com/" not in content
    assert "display=inline" in content
    # Production URLs should NOT be present
    assert "https://storage.googleapis.com/" not in content


@patch("backend.web.handlers.admin.api_history.get_files")
def test_api_history_no_files(
    mock_get_files: Mock,
    web_client: Client,
    login_gae_admin,
) -> None:
    """Test that api_history handles empty directory gracefully"""
    helpers.preseed_event("2020nyny")

    # Mock empty cloud storage
    mock_get_files.return_value = []

    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 200

    # Page should render with "No responses found" messages for all sections
    content = resp.data.decode("utf-8")
    assert "No responses found" in content
    assert "Event Details" in content


@patch("backend.web.handlers.admin.api_history.get_files")
def test_api_history_storage_error(
    mock_get_files: Mock,
    web_client: Client,
    login_gae_admin,
) -> None:
    """Test that api_history handles storage errors gracefully"""
    helpers.preseed_event("2020nyny")

    # Mock storage error
    mock_get_files.side_effect = Exception("Storage error")

    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 200

    # Page should still render with "No responses found" messages
    content = resp.data.decode("utf-8")
    assert "No responses found" in content


def test_api_history_has_tabs(web_client: Client, login_gae_admin) -> None:
    """Test that all three tabs are present in the template"""
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/admin/api_history/2020nyny")
    assert resp.status_code == 200

    content = resp.data.decode("utf-8")
    assert "FRC API" in content
    assert "FMS Reports" in content
    assert "Companion DB" in content
