import json

from backend.common.queries.dict_converters.match_converter import MatchConverter


class TestDataImporter(object):
    @staticmethod
    def import_match(path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)

        match = MatchConverter.dictToModel_v3(data)
        match.put()
