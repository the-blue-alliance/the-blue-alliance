from pyre_extensions import JSON

from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


class FMSAPISimpleJsonParser(ParserJSON[dict[str, JSON]]):
    """
    This is a parser that simply returns the raw data received from the API
    """

    def parse(self, response: dict[str, JSON]) -> dict[str, JSON]:
        return response
