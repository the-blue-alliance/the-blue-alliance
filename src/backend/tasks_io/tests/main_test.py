def test_app() -> None:
    from backend.tasks_io.main import app

    assert app is not None
