from typing import Optional

import requests

from backend.common.sitevars.fms_api_secrets import FMSApiSecrets


class FRCAPI:
    class ValidationError(Exception):
        pass

    @classmethod
    def with_credentials(cls, username: str, authkey: str):
        auth_token = FMSApiSecrets.generate_auth_token(username, authkey)
        return cls(auth_token)

    def __init__(self, auth_token: Optional[str] = None):
        # Load auth_token from Sitevar if not specified
        if not auth_token:
            auth_token = FMSApiSecrets.auth_token()

        if not auth_token:
            raise Exception(
                f"Missing FRC API auth token. Setup {FMSApiSecrets.key()} sitevar."
            )

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Basic {auth_token}"})

    def root(self) -> requests.Response:
        return self._get("/")

    def _get(self, endpoint: str) -> requests.Response:
        # Remove any leading / - we'll add it later (safer then adding a slash)
        endpoint = endpoint.lstrip("/")

        url = f"https://frc-api.firstinspires.org/v3.0/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
        }

        return self.session.get(url, headers=headers)
