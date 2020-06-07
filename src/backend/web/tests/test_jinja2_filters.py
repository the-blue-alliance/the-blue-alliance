import pytest
from backend.web import jinja2_filters as filters
from datetime import datetime
from flask import Flask
from typing import Any, Optional


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
    assert filters.strftime(datetime, "%t") == output


def test_strftime_leading_zero() -> None:
    d = datetime(2020, 2, 1)
    # Strip leading zeros
    assert datetime.strftime(d, "%d") == "01"
    assert filters.strftime(d, "%d") == "1"
    # Strip leading zeros between spaced components
    assert datetime.strftime(d, "%m, %d") == "02, 01"
    assert filters.strftime(d, "%m, %d") == "2, 1"


@pytest.mark.parametrize("input, digits, output", [(1.00001, 1, 1.0), (1.019, 2, 1.02)])
def test_floatformat(input: float, digits: int, output: float) -> None:
    assert filters.floatformat(input, digits) == str(output)


@pytest.mark.parametrize("input, output", [(None, ""), ("", ""), ("frc254", "254")])
def test_strip_frc(input: Optional[str], output: str) -> None:
    assert filters.strip_frc(input) == output


@pytest.mark.parametrize(
    "input, output",
    [(None, ""), ("", ""), (123, 123), ("123", "123"), ("abc123", "123")],
)
def test_digits(input: Any, output: Any) -> None:
    assert filters.digits(input) == output


@pytest.mark.parametrize("input, output", [(0.1, 10), (0.0, 5), (0.188, 19)])
def test_limit_prob(input: float, output: int) -> None:
    assert filters.limit_prob(input) == output


@pytest.mark.parametrize(
    "input, output", [("abc 123", "abc-123"), ("abc_123", "abc_123")]
)
def test_slugify(input: str, output: str) -> None:
    assert filters.slugify(input) == output


def test_register_template_filters(empty_app: Flask) -> None:
    for filter in filters._filters:
        assert filter not in empty_app.jinja_env.filters

    filters.register_template_filters(empty_app)

    for filter, func in filters._filters.items():
        assert filter in empty_app.jinja_env.filters
        assert empty_app.jinja_env.filters[filter] == func
