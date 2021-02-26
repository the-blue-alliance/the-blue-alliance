from flask import Flask
from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items) -> None:
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def install_url_converters(app: Flask) -> None:
    # Also install custom url converters
    app.url_map.converters["regex"] = RegexConverter
