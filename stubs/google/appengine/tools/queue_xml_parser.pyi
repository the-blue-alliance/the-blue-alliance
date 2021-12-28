from google.appengine.tools import xml_parser_utils as xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException as AppEngineConfigException
from typing import Any

PUSH_QUEUE_TAGS: Any
PUSH_QUEUE_RETRY_PARAMS: Any
RETRY_PARAMETER_TAGS: Any
BAD_MODE_ERROR_MESSAGE: str
PULL_QUEUE_ERROR_MESSAGE: str
RETRY_PARAM_ERROR_MESSAGE: str

def GetQueueYaml(unused_application, queue_xml_str): ...

class QueueXmlParser:
    errors: Any
    queue_xml: Any
    def ProcessXml(self, xml_str): ...
    def ProcessQueueNode(self, node) -> None: ...

class QueueXml:
    queues: Any
    total_storage_limit: Any
    def __init__(self) -> None: ...
    def ToYaml(self): ...

class Queue:
    def GetYamlStatementsList(self): ...

class PushQueue(Queue):
    def GetAdditionalYamlStatementsList(self): ...

class PullQueue(Queue):
    def GetAdditionalYamlStatementsList(self): ...

class Acl:
    def GetYamlStatementsList(self): ...

class RetryParameters:
    def GetYamlStatementsList(self): ...

def main() -> None: ...
