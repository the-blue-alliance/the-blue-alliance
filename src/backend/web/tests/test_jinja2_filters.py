from datetime import datetime
from flask import Flask
import pytest
from backend.web.jinja2_filters import _filters, strftime, register_template_filters


@pytest.mark.parametrize(
    "datetime, output",
    [
        (datetime(2020, 2, 1), "st"),
        (datetime(2020, 2, 2), "nd"),
        (datetime(2020, 2, 3), "rd"),
        (datetime(2020, 2, 4), "th"),
        (datetime(2020, 2, 5), "th"),
        (datetime(2020, 2, 11), "th"),
        (datetime(2020, 2, 12), "th"),
        (datetime(2020, 2, 13), "th"),
        (datetime(2020, 2, 14), "th"),
    ],
)
def test_strftime_t(datetime: datetime, output: str) -> None:
    assert strftime(datetime, "%t") == output


def test_strftime_leading_zero() -> None:
    d = datetime(2020, 2, 1)
    # Strip leading zeros
    assert datetime.strftime(d, "%d") == "01"
    assert strftime(d, "%d") == "1"
    # Strip leading zeros between spaced components
    assert datetime.strftime(d, "%m, %d") == "02, 01"
    assert strftime(d, "%m, %d") == "2, 1"


def test_register_template_filters(empty_app: Flask) -> None:
    for filter in _filters:
        assert filter not in empty_app.jinja_env.filters

    register_template_filters(empty_app)

    for filter, func in _filters.items():
        assert filter in empty_app.jinja_env.filters
        assert empty_app.jinja_env.filters[filter] == func
