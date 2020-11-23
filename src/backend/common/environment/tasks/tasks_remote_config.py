from dataclasses import dataclass


@dataclass
class TasksRemoteConfig:
    ngrok_url: str
