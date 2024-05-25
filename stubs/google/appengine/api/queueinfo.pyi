from google.appengine.api import appinfo as appinfo, validation as validation, yaml_builder as yaml_builder, yaml_listener as yaml_listener, yaml_object as yaml_object
from typing import Any

MODULE_ID_RE_STRING: str
MODULE_VERSION_RE_STRING: str
QUEUE: str
NAME: str
RATE: str
BUCKET_SIZE: str
MODE: str
TARGET: str
MAX_CONCURRENT_REQUESTS: str
TOTAL_STORAGE_LIMIT: str
RESUME_PAUSED_QUEUES: str
BYTE_SUFFIXES: str
RETRY_PARAMETERS: str
TASK_RETRY_LIMIT: str
TASK_AGE_LIMIT: str
MIN_BACKOFF_SECONDS: str
MAX_BACKOFF_SECONDS: str
MAX_DOUBLINGS: str
ACL: str
USER_EMAIL: str
WRITER_EMAIL: str

class MalformedQueueConfiguration(Exception): ...

class RetryParameters(validation.Validated):
    ATTRIBUTES: Any

class Acl(validation.Validated):
    ATTRIBUTES: Any

class QueueEntry(validation.Validated):
    ATTRIBUTES: Any

class QueueInfoExternal(validation.Validated):
    ATTRIBUTES: Any

def LoadSingleQueue(queue_info, open_fn: Any | None = ...): ...
def ParseRate(rate): ...
def ParseTotalStorageLimit(limit): ...
def ParseTaskAgeLimit(age_limit): ...
def TranslateRetryParameters(retry): ...
