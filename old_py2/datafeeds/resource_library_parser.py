import re

from datafeeds.parser_base import ParserBase
from helpers.youtube_video_helper import YouTubeVideoHelper

from bs4 import BeautifulSoup


class ResourceLibraryParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the Hall of Fame teams table.
        """
        soup = BeautifulSoup(html, "html.parser")

        tables = soup.findAll('table')

        teams = self.parseTeams(tables[0])

        return teams, False

    @classmethod
    def parseTeams(self, table):
        teams = []
        for tr in table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) < 5:
                continue

            year_str = tds[0].getText()
            if not year_str.isdigit():
                continue

            team_num = re.search(r'^Team ([0-9]+)', tds[1].getText()).group(1)
            if not team_num.isdigit():
                continue

            video = tds[2].find('a')
            if video:
                video = YouTubeVideoHelper.parse_id_from_url(video['href'])

            presentation = tds[3].find('a')
            if presentation:
                presentation = YouTubeVideoHelper.parse_id_from_url(presentation['href'])

            essay = tds[4].find('a')
            if essay:
                essay = essay['href']

                if essay[0] == '/':
                    essay = 'https://www.firstinspires.org' + essay

            teams.append({
                'team_id': 'frc' + team_num,
                'team_number': int(team_num),
                'year': int(year_str),
                'video': video,
                'presentation': presentation,
                'essay': essay,
            })

        return teams if teams != [] else None
