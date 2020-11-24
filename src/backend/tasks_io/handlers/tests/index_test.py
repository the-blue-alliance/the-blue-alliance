from flask.testing import FlaskClient


def test_app_prefix(tasks_io_client: FlaskClient) -> None:
    response = tasks_io_client.get("/tasks-io")
    assert response.status_code == 404
    # parsed_response = urlparse(response.headers["Location"])
    # assert parsed_response.path == "/account/login"
