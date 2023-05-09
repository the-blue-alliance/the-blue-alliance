from flask import Flask
from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    key: str = "regex"

    def __init__(self, url_map, *items) -> None:
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def install_url_converters(app: Flask) -> None:
    # Also install custom url converters
    install_regex_url_converter(app)


def has_regex_url_converter(app: Flask) -> bool:
    return app.url_map.converters.get(RegexConverter.key) is not None


def install_regex_url_converter(app: Flask) -> None:
    app.url_map.converters[RegexConverter.key] = RegexConverter
