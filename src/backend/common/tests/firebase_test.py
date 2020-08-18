from backend.common.firebase import app


def test_no_app() -> None:
    a = app()
    assert a is not None


def test_app() -> None:
    a = app()
    b = app()
    assert a == b
