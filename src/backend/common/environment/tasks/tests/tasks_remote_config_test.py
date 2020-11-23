from backend.common.environment.tasks.tasks_remote_config import TasksRemoteConfig


def test_ngrok_url() -> None:
    ngrok_url = "http://1d03c3c73356.ngrok.io"
    tasks_remote_config = TasksRemoteConfig(ngrok_url=ngrok_url)
    assert tasks_remote_config.ngrok_url == ngrok_url
