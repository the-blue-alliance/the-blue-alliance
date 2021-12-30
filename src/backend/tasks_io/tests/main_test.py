from backend.tasks_io.handlers.frc_api import blueprint as frc_api_blueprint


def test_app() -> None:
    from backend.tasks_io.main import app

    assert app is not None


def test_app_blueprints_frc_api() -> None:
    from backend.tasks_io.main import app

    assert app.blueprints["frc_api"] == frc_api_blueprint
