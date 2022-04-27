from typing import Dict

from pyre_extensions import JSON

from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


class FMSAPISimpleJsonParser(ParserJSON[Dict[str, JSON]]):
    """
    This is a parser that simply returns the raw data received from the API
    """

    def parse(self, response: Dict[str, JSON]) -> Dict[str, JSON]:
        return response
