import contextlib
import os

from google.cloud import ndb


@contextlib.contextmanager
def connect_to_ndb():
    if "DATASTORE_EMULATOR_HOST" in os.environ:
        print(
            f"Connecting to local datastore at {os.environ.get('DATASTORE_EMULATOR_HOST')}"
        )
    else:
        print(
            f"Connecting to NDB using keyfile {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}"
        )
    ndb_client = ndb.Client()
    with ndb_client.context():
        yield
