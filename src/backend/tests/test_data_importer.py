import json
import os
from typing import List

from backend.common.models.match import Match
from backend.common.queries.dict_converters.match_converter import MatchConverter


class TestDataImporter(object):
    @staticmethod
    def _get_path(base_path: str, path: str) -> str:
        base_dir = os.path.dirname(base_path)
        return os.path.join(base_dir, f"{path}")

    @classmethod
    def import_match(cls, base_path: str, path: str) -> None:
        with open(cls._get_path(base_path, path), "r") as f:
            data = json.load(f)

        match = MatchConverter.dictToModel_v3(data)
        match.put()

    @classmethod
    def parse_match_list(cls, base_path: str, path: str) -> List[Match]:
        with open(cls._get_path(base_path, path), "r") as f:
            data = json.load(f)

        matches = [MatchConverter.dictToModel_v3(m) for m in data]
        return matches
