"""
Tests for the add_fms_companion_db handler
"""

import datetime
import hashlib
import io
import random
import string
from typing import List, Optional, Tuple
from unittest.mock import Mock, patch

import pytest
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
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey


@pytest.fixture(autouse=True)
def no_stored_companion_db(monkeypatch: MonkeyPatch) -> None:
    # Keep the handler off the real GCS client; tests needing a stored DB override this.
    monkeypatch.setattr(
        FMSCompanionHelper,
        "get_newest_file_path",
        staticmethod(lambda event_key: None),
    )


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


def create_sqlite_db() -> bytes:
    """Create a minimal valid SQLite database file for testing"""
    # SQLite database files start with the magic string "SQLite format 3"
    # followed by a null byte, then version info
    return b"SQLite format 3\x00" + b"\x00" * 100


@freeze_time("2019-06-01")
def test_upload_companion_db_success(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test successfully uploading a FMS Companion database"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    with patch(
        "backend.common.helpers.fms_companion_helper.storage_write"
    ) as mock_write:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
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
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

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
def test_upload_invalid_sqlite_file(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with invalid SQLite file"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = b"This is not a SQLite database file"
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="notadb.db",
        content_type="application/octet-stream",
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
            "companionDb": file_storage,
            "fileDigest": file_digest,
        },
    )

    assert resp.status_code == 400
    assert "not valid" in resp.json["Error"]


@freeze_time("2019-06-01")
def test_upload_wrong_permission(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with wrong permission type"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_RANKINGS],  # Wrong permission for companion db
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
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
            "companionDb": file_storage,
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
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    wrong_digest = hashlib.sha256(b"wrong content").hexdigest()
    correct_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
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
            "companionDb": file_storage,
            "fileDigest": wrong_digest,
        },
    )

    assert resp.status_code == 401
    assert "File digest does not match" in resp.json["Error"]


@freeze_time("2019-06-01")
def test_upload_with_metadata(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test that upload includes proper metadata"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    with patch(
        "backend.common.helpers.fms_companion_helper.storage_write"
    ) as mock_write:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
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

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    resp = api_client.post(
        request_path,
        data={
            "companionDb": file_storage,
            "fileDigest": file_digest,
        },
    )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_upload_with_different_filename_and_extensions(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test uploading with different database filenames and extensions"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    # Test with .sqlite3 extension
    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="fms_data.sqlite3",
        content_type="application/octet-stream",
    )

    with patch(
        "backend.common.helpers.fms_companion_helper.storage_write"
    ) as mock_write:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
                "fileDigest": file_digest,
            },
        )

    assert resp.status_code == 200
    mock_write.assert_called_once()
    call_args = mock_write.call_args
    # Verify the path includes the filename and extension
    storage_path = call_args[0][0]
    assert "fms_data" in storage_path
    assert ".sqlite3" in storage_path


@freeze_time("2019-06-01")
def test_upload_stores_in_correct_bucket(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test that files are stored in the correct bucket"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    with patch(
        "backend.common.helpers.fms_companion_helper.storage_write"
    ) as mock_write:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
                "fileDigest": file_digest,
            },
        )

    assert resp.status_code == 200
    mock_write.assert_called_once()
    call_args = mock_write.call_args
    assert call_args[1]["bucket"] == FMSCompanionHelper.get_bucket()


@freeze_time("2019-06-01")
def test_upload_storage_path_format(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Test that storage path is formatted correctly with timestamp"""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    with patch(
        "backend.common.helpers.fms_companion_helper.storage_write"
    ) as mock_write:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
                "fileDigest": file_digest,
            },
        )

    assert resp.status_code == 200
    mock_write.assert_called_once()
    call_args = mock_write.call_args
    storage_path = call_args[0][0]

    # Verify path format: fms_companion/{event_key}/{filename}.{timestamp}{extension}
    assert storage_path.startswith("fms_companion/2019nyny/")
    assert "2019-06-01" in storage_path  # ISO format timestamp
    assert ".db" in storage_path


@freeze_time("2019-06-01")
def test_upload_missing_file_as_admin(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """Admins skip the trusted-API file check, so the handler itself must
    reject a request with no companion database file."""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[], is_admin=True)

    resp = api_client.post(
        "/api/_eventwizard/event/2019nyny/fms_companion_db",
        data={},
    )

    assert resp.status_code == 400
    assert resp.json == {"Error": "Missing FMS Companion database file"}


@freeze_time("2019-06-01")
def test_upload_as_admin_without_auth_id_skips_cloudrun_job(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """An admin session needs no X-TBA-Auth-Id header; without one the
    companion import job cannot be started, so no job params are returned."""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[], is_admin=True)

    file_content = create_sqlite_db()
    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    with (
        patch(
            "backend.common.helpers.fms_companion_helper.storage_write"
        ) as mock_write,
        patch("backend.api.handlers.eventwizard_internal.start_job") as mock_start_job,
    ):
        resp = api_client.post(
            "/api/_eventwizard/event/2019nyny/fms_companion_db",
            data={"companionDb": file_storage},
        )

    assert resp.status_code == 200
    mock_write.assert_called_once()
    mock_start_job.assert_not_called()
    assert resp.json["Success"] == "FMS Companion database successfully uploaded"
    assert resp.json["storage_path"].startswith(
        f"{FMSCompanionHelper.get_bucket()}/fms_companion/2019nyny/"
    )
    assert "job_name" not in resp.json
    assert "execution_id" not in resp.json


@freeze_time("2019-06-01")
def test_upload_duplicate_db_reuses_newest_path(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """When the upload matches the newest stored database, nothing new is
    written and the import job points at the existing file."""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    newest_path = "fms_companion/2019nyny/existing.db"
    monkeypatch.setattr(
        FMSCompanionHelper,
        "read_newest_companion_db",
        staticmethod(lambda event_key: file_content),
    )
    monkeypatch.setattr(
        FMSCompanionHelper,
        "get_newest_file_path",
        staticmethod(lambda event_key: newest_path),
    )

    with (
        patch(
            "backend.common.helpers.fms_companion_helper.storage_write"
        ) as mock_write,
        patch(
            "backend.api.handlers.eventwizard_internal.start_job",
            return_value="exec-123",
        ) as mock_start_job,
    ):
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
                "fileDigest": file_digest,
            },
        )

    expected_path = f"{FMSCompanionHelper.get_bucket()}/{newest_path}"
    assert resp.status_code == 200
    mock_write.assert_not_called()
    assert resp.json["storage_path"] == expected_path
    mock_start_job.assert_called_once()
    assert mock_start_job.call_args[1]["args"] == [f"gs://{expected_path}"]
    assert resp.json["execution_id"] == "exec-123"


@freeze_time("2019-06-01")
def test_upload_duplicate_db_with_unknown_newest_path_does_not_start_job(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """A duplicate upload whose stored path is unknown starts no import job."""
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    file_content = create_sqlite_db()
    file_digest = hashlib.sha256(file_content).hexdigest()

    request_path = "/api/_eventwizard/event/2019nyny/fms_companion_db"

    file_storage = FileStorage(
        stream=io.BytesIO(file_content),
        filename="companion.db",
        content_type="application/octet-stream",
    )

    monkeypatch.setattr(
        FMSCompanionHelper,
        "read_newest_companion_db",
        staticmethod(lambda event_key: file_content),
    )
    monkeypatch.setattr(
        FMSCompanionHelper,
        "get_newest_file_path",
        staticmethod(lambda event_key: None),
    )

    with patch(
        "backend.api.handlers.eventwizard_internal.start_job",
        return_value="exec-123",
    ) as mock_start_job:
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, file_digest
                ),
            },
            data={
                "companionDb": file_storage,
                "fileDigest": file_digest,
            },
        )

    mock_start_job.assert_not_called()
    assert resp.json.get("storage_path") != ""
