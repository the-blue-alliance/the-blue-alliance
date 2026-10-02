import json

from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict


def test_lazy_load_json() -> None:
    j = {"abc": "def"}
    suggestion = Suggestion(contents_json=json.dumps(j))
    assert suggestion.contents == j


def test_lazy_sets_json() -> None:
    suggestion = Suggestion()
    j: SuggestionDict = {"media_type_enum": MediaType.YOUTUBE_VIDEO}
    suggestion.contents = j
    assert suggestion.contents_json == json.dumps(j)


def test_shadow_banned() -> None:
    account = Account(id="abc", shadow_banned=True)

    suggestion = Suggestion(author=account.put(), target_model=SuggestionType.ROBOT)
    suggestion.put()
    assert suggestion.review_state == SuggestionState.REVIEW_AUTOREJECTED


def test_not_shadow_banned() -> None:
    account = Account(id="abc")

    suggestion = Suggestion(author=account.put(), target_model=SuggestionType.ROBOT)
    suggestion.put()
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING


def test_youtube_video() -> None:
    suggestion = Suggestion(
        contents_json=json.dumps({"youtube_videos": ["abc123", "def456"]})
    )
    assert suggestion.youtube_video == "abc123"


def test_youtube_video_missing() -> None:
    suggestion = Suggestion(contents_json=json.dumps({"abc": "def"}))
    assert suggestion.youtube_video is None


def test_candidate_media() -> None:
    suggestion = Suggestion(
        contents_json=json.dumps(
            {
                "reference_type": "team",
                "reference_key": "frc254",
                "media_type_enum": MediaType.YOUTUBE_VIDEO,
                "foreign_key": "abc123",
                "year": 2019,
            }
        )
    )
    media = suggestion.candidate_media
    assert media.key_name == "youtube_abc123"
    assert media.foreign_key == "abc123"
    assert media.year == 2019
    assert media.references == [ndb.Key("Team", "frc254")]
