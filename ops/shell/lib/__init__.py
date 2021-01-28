import contextlib
import os

from google.cloud import ndb


@contextlib.contextmanager
def connect_to_ndb():
    print(
        f"Connecting to NDB using keyfile {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}"
    )
    ndb_client = ndb.Client()
    with ndb_client.context() as ndb_context:
        yield
