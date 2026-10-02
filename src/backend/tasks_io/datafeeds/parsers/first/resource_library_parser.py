import re
from typing import List, Optional, Tuple, TypedDict

from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.tasks_io.datafeeds.parsers.parser_html import ParserHTML


class ParsedHallOfFameTeam(TypedDict):
    team_id: str
    team_number: int
    year: int
    video: Optional[str]
    presentation: Optional[str]
    essay: Optional[str]


class ResourceLibraryParser(ParserHTML[Tuple[List[ParsedHallOfFameTeam], bool]]):
    SUMMARY_RE = re.compile(r"^\s*(\d{4})\s*[-–]\s*Team\s+(\d+)")

    def parse(self, response: bytes) -> Tuple[List[ParsedHallOfFameTeam], bool]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response, "html.parser")

        teams: List[ParsedHallOfFameTeam] = []
        for details in soup.find_all("details"):
            summary = details.find("summary")
            if summary is None:
                continue

            match = self.SUMMARY_RE.match(summary.get_text(" ", strip=True))
            if match is None:
                continue

            year = int(match.group(1))
            team_number = int(match.group(2))

            video: Optional[str] = None
            presentation: Optional[str] = None
            essay: Optional[str] = None

            for frame in details.find_all("iframe"):
                src = frame.get("src") or frame.get("data-src")
                if not src:
                    continue
                video = YouTubeVideoHelper.parse_id_from_url(src)
                if video is not None:
                    break

            for link in details.find_all("a"):
                href = link.get("href")
                if not href:
                    continue
                label = link.get_text(" ", strip=True).lower()

                if "essay" in label and essay is None:
                    essay = href
                    if essay.startswith("/"):
                        essay = "https://www.firstinspires.org" + essay
                elif "presentation" in label and presentation is None:
                    presentation = YouTubeVideoHelper.parse_id_from_url(href)
                elif "video" in label and video is None:
                    video = YouTubeVideoHelper.parse_id_from_url(href)

            teams.append(
                ParsedHallOfFameTeam(
                    team_id=f"frc{team_number}",
                    team_number=team_number,
                    year=year,
                    video=video,
                    presentation=presentation,
                    essay=essay,
                )
            )

        return teams, False
