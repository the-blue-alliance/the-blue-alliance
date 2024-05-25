from google.appengine.api import appinfo as appinfo, validation as validation, yaml_builder as yaml_builder, yaml_listener as yaml_listener, yaml_object as yaml_object
from google.appengine.cron import groc as groc, groctimespecification as groctimespecification
from typing import Any

SERVER_ID_RE_STRING: str
SERVER_VERSION_RE_STRING: str

class GrocValidator(validation.Validator):
    def Validate(self, value, key: Any | None = ...): ...

class TimezoneValidator(validation.Validator):
    def Validate(self, value, key: Any | None = ...): ...

CRON: str
URL: str
SCHEDULE: str
TIMEZONE: str
DESCRIPTION: str
TARGET: str
RETRY_PARAMETERS: str
JOB_RETRY_LIMIT: str
JOB_AGE_LIMIT: str
MIN_BACKOFF_SECONDS: str
MAX_BACKOFF_SECONDS: str
MAX_DOUBLINGS: str
ATTEMPT_DEADLINE: str

class AttemptDeadlineValidator(validation.Validator):
    def Validate(self, value, key: str = ...): ...

class MalformedCronfigurationFile(Exception): ...

class RetryParameters(validation.Validated):
    ATTRIBUTES: Any

class CronEntry(validation.Validated):
    ATTRIBUTES: Any

class CronInfoExternal(validation.Validated):
    ATTRIBUTES: Any

def LoadSingleCron(cron_info, open_fn: Any | None = ...): ...
