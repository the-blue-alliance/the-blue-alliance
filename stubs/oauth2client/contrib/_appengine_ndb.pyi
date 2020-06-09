from google.appengine.ext import ndb
from oauth2client import client as client
from typing import Any

NDB_KEY: Any
NDB_MODEL: Any

class SiteXsrfSecretKeyNDB(ndb.Model):
    secret: Any = ...

class FlowNDBProperty(ndb.PickleProperty): ...
class CredentialsNDBProperty(ndb.BlobProperty): ...

class CredentialsNDBModel(ndb.Model):
    credentials: Any = ...
