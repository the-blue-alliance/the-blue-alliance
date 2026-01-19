"""
Tests for the add_fms_report_archive handler
"""

import datetime
import hashlib
import io
import random
import string
from typing import List, Optional, Tuple
from unittest.mock import Mock, patch

from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from pytest import MonkeyPatch
from werkzeug.datastructures import FileStorage
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common import auth
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey


def setup_event(event_type: EventType = EventType.OFFSEASON) -> None:
    Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=event_type,
    ).put()


def setup_user(
    monkeypatch: MonkeyPatch,
    permissions: List = [],
    is_admin: bool = False,
) -> ndb.Key:
    email = "zach@thebluealliance.com"
    account = Account(
        email=email,
        permissions=permissions,
    )
    account.put()

    monkeypatch.setattr(
        auth, "_decoded_claims", Mock(return_value={"email": email, "admin": is_admin})
    )
    return account.key


def setup_api_auth(
    event_key: Optional[EventKey],
    auth_types: List[AuthType] = [],
    expiration: Optional[datetime.datetime] = None,
) -> Tuple[str, str]:
    auth = ApiAuthAccess(
        id="".join(random.choices(string.ascii_letters + string.digits, k=10)),
        secret="".join(random.choices(string.ascii_letters + string.digits, k=10)),
        event_list=[ndb.Key(Event, event_key)] if event_key else [],
        auth_types_enum=auth_types,
        expiration=expiration,
    )
    auth.put()

    return none_throws(auth.key.string_id()), none_throws(auth.secret)


def create_excel_file() -> bytes:
    """Create a minimal valid Excel file for testing"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws["A1"] = "Test Data"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()


@freeze_time("2019-06-01")
def test_upload_qual_rankings_success(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test successfully uploading a qual_rankings FMS report"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    file_content = create_excel_file()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    with patch("backend.common.helpers.fms_report_helper.storage_write") as mock_write:
        with patch(
            "backend.common.helpers.fms_report_helper.storage_get_files"
        ) as mock_get_files:
            mock_get_files.return_value = []

            resp = api_client.post(
                request_path,
                headers={
                    "X-TBA-Auth-Id": auth_id,
                    "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                        auth_secret, request_path, file_digest
                    ),
                },
                data={
                    "reportFile": file_storage,
                    "fileDigest": file_digest,
                },
            )

    assert resp.status_code == 200
    assert "Success" in resp.json
    mock_write.assert_called_once()


@freeze_time("2019-06-01")
def test_upload_missing_file(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with missing file"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    resp = api_client.post(
        request_path,
        headers={
            "X-TBA-Auth-Id": auth_id,
            "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                auth_secret, request_path, ""
            ),
        },
        data={},
    )

    assert resp.status_code == 401
    assert "Expected file upload not found" in resp.json["Error"]


@freeze_time("2019-06-01")
def test_upload_invalid_excel_file(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with invalid Excel file"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    file_content = b"This is not an Excel file"
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="notexcel.xlsx",
        content_type="application/vnd.ms-excel",
    )

    resp = api_client.post(
        request_path,
        headers={
            "X-TBA-Auth-Id": auth_id,
            "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                auth_secret, request_path, file_digest
            ),
        },
        data={
            "reportFile": file_storage,
            "fileDigest": file_digest,
        },
    )

    assert resp.status_code == 400
    assert "not a valid Excel file" in resp.json["Error"]


@freeze_time("2019-06-01")
def test_upload_wrong_permission(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with wrong permission type"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],  # Wrong permission for qual_rankings
        expiration=None,
    )

    file_content = create_excel_file()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    resp = api_client.post(
        request_path,
        headers={
            "X-TBA-Auth-Id": auth_id,
            "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                auth_secret, request_path, file_digest
            ),
        },
        data={
            "reportFile": file_storage,
            "fileDigest": file_digest,
        },
    )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_upload_mismatched_digest(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with mismatched file digest"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    file_content = create_excel_file()
    wrong_digest = hashlib.sha256(b"wrong content").hexdigest()
    correct_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    resp = api_client.post(
        request_path,
        headers={
            "X-TBA-Auth-Id": auth_id,
            "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                auth_secret, request_path, correct_digest
            ),
        },
        data={
            "reportFile": file_storage,
            "fileDigest": wrong_digest,
        },
    )

    assert resp.status_code == 401
    assert "File digest does not match" in resp.json["Error"]


@freeze_time("2019-06-01")
def test_upload_duplicate_file_not_written(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test that duplicate files are not written again"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    file_content = create_excel_file()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    # Simulate that the file already exists with the exact filename format
    # mtime format is 2019-06-01 00:00:00
    existing_files = [
        "fms_reports/2019nyny/qual_rankings/rankings.2019-06-01 00:00:00.xlsx"
    ]

    with patch("backend.common.helpers.fms_report_helper.storage_write") as mock_write:
        with patch(
            "backend.common.helpers.fms_report_helper.storage_get_files"
        ) as mock_get_files:
            mock_get_files.return_value = existing_files

            resp = api_client.post(
                request_path,
                headers={
                    "X-TBA-Auth-Id": auth_id,
                    "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                        auth_secret, request_path, file_digest
                    ),
                },
                data={
                    "reportFile": file_storage,
                    "fileDigest": file_digest,
                },
            )

    assert resp.status_code == 200
    # storage_write should not be called since the file already exists
    mock_write.assert_not_called()


@freeze_time("2019-06-01")
def test_upload_with_metadata(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test that upload includes proper metadata"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],
        expiration=None,
    )

    file_content = create_excel_file()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    with patch("backend.common.helpers.fms_report_helper.storage_write") as mock_write:
        with patch(
            "backend.common.helpers.fms_report_helper.storage_get_files"
        ) as mock_get_files:
            mock_get_files.return_value = []

            resp = api_client.post(
                request_path,
                headers={
                    "X-TBA-Auth-Id": auth_id,
                    "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                        auth_secret, request_path, file_digest
                    ),
                },
                data={
                    "reportFile": file_storage,
                    "fileDigest": file_digest,
                },
            )

    assert resp.status_code == 200
    # Verify storage_write was called with metadata
    mock_write.assert_called_once()
    call_args = mock_write.call_args
    assert "metadata" in call_args[1]
    assert "X-TBA-Auth-Id" in call_args[1]["metadata"]
    assert call_args[1]["metadata"]["X-TBA-Auth-Id"] == auth_id


@freeze_time("2019-06-01")
def test_upload_not_authenticated(ndb_stub, api_client: Client) -> None:
    """Test uploading without authentication"""
    setup_event(event_type=EventType.OFFSEASON)

    file_content = create_excel_file()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_reports/qual_rankings"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="rankings.xlsx",
        content_type="application/vnd.ms-excel",
    )

    resp = api_client.post(
        request_path,
        data={
            "reportFile": file_storage,
            "fileDigest": file_digest,
        },
    )

    assert resp.status_code == 401
    assert "Error" in resp.json
