from typing import Dict, List, Optional

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.helpers.insights_v2.clubs.calculator import ClubV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    ClubContextType,
    HallOfFameClubContext,
    InsightV2,
)
from backend.common.models.keys import Year
from backend.common.models.media import Media

_MEDIA_TAGS = (
    MediaTag.CHAIRMANS_VIDEO,
    MediaTag.CHAIRMANS_PRESENTATION,
    MediaTag.CHAIRMANS_ESSAY,
)


class HallOfFameClubV2Calculator(ClubV2Calculator):
    """
    Teams that have won the Impact/Chairman's Award at Championship finals
    (EventType.CMP_FINALS). extra_context carries the Chairman's video,
    presentation, and essay links scraped by the Hall of Fame parser into
    CHAIRMANS_*-tagged Media rows.
    """

    def __init__(self) -> None:
        super().__init__()
        self._media_by_team: Dict[str, Dict[MediaTag, Media]] = {}

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HALL_OF_FAME

    @property
    def context_type(self) -> ClubContextType:
        return "hall_of_fame"

    def on_event(self, event: Event) -> None:
        event_key = str(event.key.id())
        for award in event.awards:
            if (
                award.award_type_enum == AwardType.CHAIRMANS
                and award.event_type_enum == EventType.CMP_FINALS
            ):
                for team_key in award.team_list:
                    self._record(str(team_key.id()), event_key)

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        if year == 0 and self._first_event:
            self._media_by_team = self._load_chairmans_media()
        return super().make_insights(year, team_to_district)

    def _load_chairmans_media(self) -> Dict[str, Dict[MediaTag, Media]]:
        by_team: Dict[str, Dict[MediaTag, Media]] = {}
        for tag in _MEDIA_TAGS:
            for media in Media.query(Media.media_tag_enum == tag).fetch():
                for ref in media.references:
                    if ref.kind() != "Team":
                        continue
                    by_team.setdefault(str(ref.id()), {}).setdefault(tag, media)
        return by_team

    def _extra_context_for(
        self, team_key: str, event_added_key: str
    ) -> Optional[HallOfFameClubContext]:
        media = self._media_by_team.get(team_key, {})
        video = media.get(MediaTag.CHAIRMANS_VIDEO)
        presentation = media.get(MediaTag.CHAIRMANS_PRESENTATION)
        essay = media.get(MediaTag.CHAIRMANS_ESSAY)
        return HallOfFameClubContext(
            year=int(event_added_key[:4]),
            video=video.youtube_url_link if video is not None else None,
            presentation=(
                presentation.youtube_url_link if presentation is not None else None
            ),
            essay=essay.external_link if essay is not None else None,
        )
