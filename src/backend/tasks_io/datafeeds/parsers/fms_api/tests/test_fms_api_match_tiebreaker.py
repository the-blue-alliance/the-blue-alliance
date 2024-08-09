import datetime
from unittest.mock import Mock

import pytest
from google.appengine.ext import ndb
from google.auth.credentials import AnonymousCredentials

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.frc_api.frc_api import FRCAPI
from backend.common.helpers.match_helper import MatchHelper
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.storage.clients.gcloud_client import GCloudStorageClient
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI

# these are coming from within the NDB library
pytestmark = pytest.mark.filterwarnings("ignore::ResourceWarning")


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub) -> None:
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


@pytest.fixture(autouse=True)
def force_prod_gcs_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.common import storage

    credentials = AnonymousCredentials()
    client_fn = Mock()
    client_fn.return_value = GCloudStorageClient(
        "tbatv-prod-hrd", credentials=credentials
    )
    monkeypatch.setattr(storage, "_client_for_env", client_fn)


def test_2017flwp_sequence(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017flwp",
        event_short="flwp",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    event_code = "flwp"

    file_prefix = "frc-api-response/v2.0/2017/schedule/{}/playoff/hybrid/".format(
        event_code
    )
    gcs_files = FRCAPI.get_cached_gcs_files(file_prefix)

    for filename in gcs_files:
        time_str = filename.replace(file_prefix, "").replace(".json", "").strip()
        file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H_%M_%S.%f")
        query_time = file_time + datetime.timedelta(seconds=30)
        MatchManipulator.createOrUpdate(
            DatafeedFMSAPI(
                sim_time=query_time, sim_api_version="v2.0"
            ).get_event_matches("2017{}".format(event_code)),
            run_post_update_hook=False,
        )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017flwp"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 7

    sf1m1 = Match.get_by_id("2017flwp_sf1m1")
    assert sf1m1 is not None
    assert sf1m1.alliances[AllianceColor.RED]["score"] == 305
    assert sf1m1.alliances[AllianceColor.BLUE]["score"] == 255

    m1_breakdown = sf1m1.score_breakdown
    assert m1_breakdown is not None
    assert m1_breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert m1_breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    sf1m2 = Match.get_by_id("2017flwp_sf1m2")
    assert sf1m2 is not None
    assert sf1m2.alliances[AllianceColor.RED]["score"] == 165
    assert sf1m2.alliances[AllianceColor.BLUE]["score"] == 258

    m2_breakdown = sf1m2.score_breakdown
    assert m2_breakdown is not None
    assert m2_breakdown[AllianceColor.RED]["totalPoints"] == 165
    assert m2_breakdown[AllianceColor.BLUE]["totalPoints"] == 258

    sf1m3 = Match.get_by_id("2017flwp_sf1m3")
    assert sf1m3 is not None
    assert sf1m3.alliances[AllianceColor.RED]["score"] == 255
    assert sf1m3.alliances[AllianceColor.BLUE]["score"] == 255

    m3_breakdown = sf1m3.score_breakdown
    assert m3_breakdown is not None
    assert m3_breakdown[AllianceColor.RED]["totalPoints"] == 255
    assert m3_breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    sf1m4 = Match.get_by_id("2017flwp_sf1m4")
    assert sf1m4 is not None
    assert sf1m4.alliances[AllianceColor.RED]["score"] == 255
    assert sf1m4.alliances[AllianceColor.BLUE]["score"] == 255

    m4_breakdown = sf1m4.score_breakdown
    assert m4_breakdown is not None
    assert m4_breakdown[AllianceColor.RED]["totalPoints"] == 255
    assert m4_breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    sf1m5 = Match.get_by_id("2017flwp_sf1m5")
    assert sf1m5 is not None
    assert sf1m5.alliances[AllianceColor.RED]["score"] == 165
    assert sf1m5.alliances[AllianceColor.BLUE]["score"] == 263

    m5_breakdown = sf1m5.score_breakdown
    assert m5_breakdown is not None
    assert m5_breakdown[AllianceColor.RED]["totalPoints"] == 165
    assert m5_breakdown[AllianceColor.BLUE]["totalPoints"] == 263


def test_2017flwp(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017flwp",
        event_short="flwp",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 21, 22), sim_api_version="v2.0"
        ).get_event_matches("2017flwp")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017flwp"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 5
    old_match = Match.get_by_id("2017flwp_sf1m3")
    assert old_match is not None
    assert old_match.alliances[AllianceColor.RED]["score"] == 255
    assert old_match.alliances[AllianceColor.BLUE]["score"] == 255

    breakdown = old_match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 255
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 21, 35), sim_api_version="v2.0"
        ).get_event_matches("2017flwp")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017flwp"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 6
    new_match = Match.get_by_id("2017flwp_sf1m3")
    assert new_match is not None

    assert old_match.alliances == new_match.alliances
    assert old_match.score_breakdown == new_match.score_breakdown

    tiebreaker_match = Match.get_by_id("2017flwp_sf1m4")
    assert tiebreaker_match is not None

    assert tiebreaker_match.alliances[AllianceColor.RED]["score"] == 165
    assert tiebreaker_match.alliances[AllianceColor.BLUE]["score"] == 263

    breakdown = tiebreaker_match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 165
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 263


def test_2017pahat(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017pahat",
        event_short="pahat",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    matches = DatafeedFMSAPI(
        sim_time=datetime.datetime(2017, 3, 5, 20, 45), sim_api_version="v2.0"
    ).get_event_matches("2017pahat")
    MatchManipulator.createOrUpdate(matches)

    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    f_matches = Match.query(
        Match.event == ndb.Key(Event, "2017pahat"), Match.comp_level == CompLevel.F
    ).fetch()
    assert len(f_matches) == 3
    old_match = Match.get_by_id("2017pahat_f1m2")
    assert old_match is not None
    assert old_match.alliances[AllianceColor.RED]["score"] == 255
    assert old_match.alliances[AllianceColor.BLUE]["score"] == 255
    breakdown = old_match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 255
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 5, 21, 2), sim_api_version="v2.0"
        ).get_event_matches("2017pahat")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    f_matches = Match.query(
        Match.event == ndb.Key(Event, "2017pahat"), Match.comp_level == "f"
    ).fetch()
    assert len(f_matches) == 4
    new_match = Match.get_by_id("2017pahat_f1m2")
    assert new_match is not None

    assert old_match.alliances == new_match.alliances
    assert old_match.score_breakdown == new_match.score_breakdown

    tiebreaker_match = Match.get_by_id("2017pahat_f1m4")
    assert tiebreaker_match is not None

    assert tiebreaker_match.alliances[AllianceColor.RED]["score"] == 240
    assert tiebreaker_match.alliances[AllianceColor.BLUE]["score"] == 235
    breakdown = tiebreaker_match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 240
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 235


def test_2017scmb_sequence(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017scmb",
        event_short="scmb",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    event_code = "scmb"

    file_prefix = "frc-api-response/v2.0/2017/schedule/{}/playoff/hybrid/".format(
        event_code
    )

    gcs_files = FRCAPI.get_cached_gcs_files(file_prefix)
    for filename in gcs_files:
        time_str = filename.replace(file_prefix, "").replace(".json", "").strip()
        file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H_%M_%S.%f")
        query_time = file_time + datetime.timedelta(seconds=30)
        MatchManipulator.createOrUpdate(
            DatafeedFMSAPI(
                sim_time=query_time, sim_api_version="v2.0"
            ).get_event_matches("2017{}".format(event_code)),
            run_post_update_hook=False,
        )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    qf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "qf"
    ).fetch()
    assert len(qf_matches) == 11

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 4

    f_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "f"
    ).fetch()
    assert len(f_matches) == 3

    qf4m1 = Match.get_by_id("2017scmb_qf4m1")
    assert qf4m1 is not None
    assert qf4m1.alliances[AllianceColor.RED]["score"] == 305
    assert qf4m1.alliances[AllianceColor.BLUE]["score"] == 305

    m1_breakdown = qf4m1.score_breakdown
    assert m1_breakdown is not None
    assert m1_breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert m1_breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    qf4m2 = Match.get_by_id("2017scmb_qf4m2")
    assert qf4m2 is not None
    assert qf4m2.alliances[AllianceColor.RED]["score"] == 213
    assert qf4m2.alliances[AllianceColor.BLUE]["score"] == 305

    m2_breakdown = qf4m2.score_breakdown
    assert m2_breakdown is not None
    assert m2_breakdown[AllianceColor.RED]["totalPoints"] == 213
    assert m2_breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    qf4m3 = Match.get_by_id("2017scmb_qf4m3")
    assert qf4m3 is not None
    assert qf4m3.alliances[AllianceColor.RED]["score"] == 312
    assert qf4m3.alliances[AllianceColor.BLUE]["score"] == 255

    m3_breakdown = qf4m3.score_breakdown
    assert m3_breakdown is not None
    assert m3_breakdown[AllianceColor.RED]["totalPoints"] == 312
    assert m3_breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    qf4m4 = Match.get_by_id("2017scmb_qf4m4")
    assert qf4m4 is not None
    assert qf4m4.alliances[AllianceColor.RED]["score"] == 310
    assert qf4m4.alliances[AllianceColor.BLUE]["score"] == 306

    m4_breakdown = qf4m4.score_breakdown
    assert m4_breakdown is not None
    assert m4_breakdown[AllianceColor.RED]["totalPoints"] == 310
    assert m4_breakdown[AllianceColor.BLUE]["totalPoints"] == 306


def test_2017scmb(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017scmb",
        event_short="scmb",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 19, 17), sim_api_version="v2.0"
        ).get_event_matches("2017scmb")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    qf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "qf"
    ).fetch()
    assert len(qf_matches) == 12

    match = Match.get_by_id("2017scmb_qf4m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 305
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 19, 50), sim_api_version="v2.0"
        ).get_event_matches("2017scmb")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    qf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "qf"
    ).fetch()
    assert len(qf_matches) == 12

    match = Match.get_by_id("2017scmb_qf4m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 305
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    match = Match.get_by_id("2017scmb_qf4m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 213
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 213
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 20, 12), sim_api_version="v2.0"
        ).get_event_matches("2017scmb")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    qf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "qf"
    ).fetch()
    assert len(qf_matches) == 12

    match = Match.get_by_id("2017scmb_qf4m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 305
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    match = Match.get_by_id("2017scmb_qf4m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 213
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 213
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    match = Match.get_by_id("2017scmb_qf4m3")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 312
    assert match.alliances[AllianceColor.BLUE]["score"] == 255

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 312
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 4, 20, 48), sim_api_version="v2.0"
        ).get_event_matches("2017scmb")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    qf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017scmb"), Match.comp_level == "qf"
    ).fetch()
    assert len(qf_matches) == 13

    match = Match.get_by_id("2017scmb_qf4m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 305
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 305
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    match = Match.get_by_id("2017scmb_qf4m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 213
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 213
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305

    match = Match.get_by_id("2017scmb_qf4m3")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 312
    assert match.alliances[AllianceColor.BLUE]["score"] == 255

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 312
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 255

    match = Match.get_by_id("2017scmb_qf4m4")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 310
    assert match.alliances[AllianceColor.BLUE]["score"] == 306

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 310
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 306


def test_2017ncwin(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2017ncwin",
        event_short="ncwin",
        year=2017,
        event_type_enum=0,
        timezone_id="America/New_York",
    )
    event.put()

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 5, 21, 2), sim_api_version="v2.0"
        ).get_event_matches("2017ncwin")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017ncwin"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 6

    match = Match.get_by_id("2017ncwin_sf2m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 265
    assert match.alliances[AllianceColor.BLUE]["score"] == 150

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 265
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 150

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 5, 21, 30), sim_api_version="v2.0"
        ).get_event_matches("2017ncwin")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017ncwin"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 6

    match = Match.get_by_id("2017ncwin_sf2m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 265
    assert match.alliances[AllianceColor.BLUE]["score"] == 150

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 265
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 150

    match = Match.get_by_id("2017ncwin_sf2m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 205
    assert match.alliances[AllianceColor.BLUE]["score"] == 205

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 205
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 205

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 5, 21, 35), sim_api_version="v2.0"
        ).get_event_matches("2017ncwin")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017ncwin"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 6

    match = Match.get_by_id("2017ncwin_sf2m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 265
    assert match.alliances[AllianceColor.BLUE]["score"] == 150

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 265
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 150

    match = Match.get_by_id("2017ncwin_sf2m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 205
    assert match.alliances[AllianceColor.BLUE]["score"] == 205

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 205
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 205

    match = Match.get_by_id("2017ncwin_sf2m3")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 145
    assert match.alliances[AllianceColor.BLUE]["score"] == 265

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 145
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 265

    ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2017, 3, 5, 21, 51), sim_api_version="v2.0"
        ).get_event_matches("2017ncwin")
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == ndb.Key(Event, "2017ncwin"), Match.comp_level == "sf"
    ).fetch()
    assert len(sf_matches) == 7

    match = Match.get_by_id("2017ncwin_sf2m1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 265
    assert match.alliances[AllianceColor.BLUE]["score"] == 150

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 265
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 150

    match = Match.get_by_id("2017ncwin_sf2m2")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 205
    assert match.alliances[AllianceColor.BLUE]["score"] == 205

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 205
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 205

    match = Match.get_by_id("2017ncwin_sf2m3")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 145
    assert match.alliances[AllianceColor.BLUE]["score"] == 265

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 145
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 265

    match = Match.get_by_id("2017ncwin_sf2m4")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["score"] == 180
    assert match.alliances[AllianceColor.BLUE]["score"] == 305

    breakdown = match.score_breakdown
    assert breakdown is not None
    assert breakdown[AllianceColor.RED]["totalPoints"] == 180
    assert breakdown[AllianceColor.BLUE]["totalPoints"] == 305


def test_2023ncash_double_elim(ndb_stub, taskqueue_stub) -> None:
    event = Event(
        id="2023ncash",
        event_short="ncash",
        year=2023,
        event_type_enum=EventType.DISTRICT,
        playoff_type=PlayoffType.DOUBLE_ELIM_8_TEAM,
        timezone_id="America/New_York",
    )
    event.put()

    # The first play for this match is a tie
    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2023, 3, 5, 20, 58), sim_api_version="v3.0"
        ).get_event_matches(event.key_name)
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == event.key, Match.comp_level == CompLevel.SF
    ).fetch()
    played_sf_matches = [m for m in sf_matches if m.has_been_played]
    assert len(played_sf_matches) == 12

    match = Match.get_by_id("2023ncash_sf12m1")
    assert match is not None
    assert match.winning_alliance == ""

    # The second play for this match had a winner
    MatchManipulator.createOrUpdate(
        DatafeedFMSAPI(
            sim_time=datetime.datetime(2023, 3, 5, 21, 19), sim_api_version="v3.0"
        ).get_event_matches(event.key_name)
    )
    _, keys_to_delete = MatchHelper.delete_invalid_matches(event.matches, event)
    MatchManipulator.delete_keys(keys_to_delete)

    sf_matches = Match.query(
        Match.event == event.key, Match.comp_level == CompLevel.SF
    ).fetch()
    played_sf_matches = [m for m in sf_matches if m.has_been_played]
    assert len(played_sf_matches) == 13

    # The first play for this match remains a tie
    match = Match.get_by_id("2023ncash_sf12m1")
    assert match is not None
    assert match.winning_alliance == ""
    assert match.verbose_name == "Match 12"

    # The second play gets added afterwards
    match = Match.get_by_id("2023ncash_sf12m2")
    assert match is not None
    assert match.winning_alliance == AllianceColor.RED
    assert match.verbose_name == "Match 12 (Play 2)"
