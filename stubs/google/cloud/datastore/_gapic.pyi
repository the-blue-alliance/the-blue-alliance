from google.cloud._helpers import make_secure_channel as make_secure_channel
from google.cloud._http import DEFAULT_USER_AGENT as DEFAULT_USER_AGENT
from google.cloud.datastore_v1.gapic import datastore_client as datastore_client
from typing import Any

def make_datastore_api(client: Any): ...
