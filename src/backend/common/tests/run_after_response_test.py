import functools
import logging
from unittest.mock import Mock

import pytest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from backend.common.run_after_response import (
    execute_callbacks,
    response_context,
    run_after_response,
)


@pytest.fixture(autouse=True)
def clean_response_context():
    if hasattr(response_context, "request"):
        del response_context.request
    yield
    if hasattr(response_context, "request"):
        del response_context.request


def test_run_after_response_outside_request_logs_debug_and_returns_callback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    callback = Mock()
    with caplog.at_level(logging.DEBUG):
        result = run_after_response(callback)

    assert result is callback
    assert "dropping callback" in caplog.text


def test_run_after_response_as_decorator() -> None:
    response_context.request = Request(create_environ(path="/"))

    @run_after_response
    def my_callback() -> str:
        return "called"

    # Decorator returns the original function so it remains callable
    assert callable(my_callback)
    assert my_callback() == "called"

    # It was also enqueued in after_response_callbacks
    callbacks = getattr(response_context.request, "after_response_callbacks", [])
    assert len(callbacks) == 1
    assert callbacks[0] is my_callback


def test_execute_callbacks_clears_list() -> None:
    response_context.request = Request(create_environ(path="/"))
    callback = Mock()
    run_after_response(callback)

    execute_callbacks()
    callback.assert_called_once()

    # Callbacks list is cleared
    assert getattr(response_context.request, "after_response_callbacks") == []

    # Second execution does not call the callback again
    execute_callbacks()
    callback.assert_called_once()


def test_execute_callbacks_handles_exceptions_and_continues(
    caplog: pytest.LogCaptureFixture,
) -> None:
    response_context.request = Request(create_environ(path="/"))
    failing_callback = Mock(side_effect=RuntimeError("something went wrong"))
    failing_callback.__name__ = "failing_callback"

    successful_callback = Mock()
    successful_callback.__name__ = "successful_callback"

    run_after_response(failing_callback)
    run_after_response(successful_callback)

    with caplog.at_level(logging.WARNING):
        execute_callbacks()

    failing_callback.assert_called_once()
    successful_callback.assert_called_once()
    assert "Callback failing_callback failed after response" in caplog.text


def test_execute_callbacks_with_partial() -> None:
    response_context.request = Request(create_environ(path="/"))

    def target_func(arg: str) -> None:
        pass

    mock_func = Mock(side_effect=target_func)
    mock_func.__name__ = "target_func"

    partial_callback = functools.partial(mock_func, "value")
    run_after_response(partial_callback)

    execute_callbacks()
    mock_func.assert_called_once_with("value")


def test_execute_callbacks_without_request() -> None:
    # Should safely return without error when no request is set
    assert not hasattr(response_context, "request")
    execute_callbacks()
