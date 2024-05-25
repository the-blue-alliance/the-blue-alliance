import logging
import re

from datafeeds.parser_base import ParserBase


class TbaVideosParser(ParserBase):
    """
    Facilitates building TBAVideos store from TBA.
    """
    @classmethod
    def parse(self, html):
        """
        Parse the directory listing on TBA to extract relevant TBAVideo
        information. Returns a list of TBAVideos
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html)

        videos = dict()

        for a in soup.findAll("a", href=True):
            parts = a["href"].split(".")
            if len(parts) == 2:
                (key, filetype) = parts
                videos.setdefault(key, list())
                videos[key].append(filetype)
            else:
                logging.info("Malformed video filename: " + a["href"])
                continue

        return videos, False
