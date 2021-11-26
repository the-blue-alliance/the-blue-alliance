from google.appengine.api import appinfo_errors as appinfo_errors, backendinfo as backendinfo, validation as validation, yaml_builder as yaml_builder, yaml_listener as yaml_listener, yaml_object as yaml_object
from typing import Any

APP_ID_MAX_LEN: int
MODULE_ID_MAX_LEN: int
MODULE_VERSION_ID_MAX_LEN: int
MAX_URL_MAPS: int
PARTITION_SEPARATOR: str
DOMAIN_SEPARATOR: str
VERSION_SEPARATOR: str
MODULE_SEPARATOR: str
DEFAULT_MODULE: str
PARTITION_RE_STRING_WITHOUT_SEPARATOR: Any
PARTITION_RE_STRING: Any
DOMAIN_RE_STRING_WITHOUT_SEPARATOR: Any
DOMAIN_RE_STRING: Any
DISPLAY_APP_ID_RE_STRING: Any
APPLICATION_RE_STRING: Any
MODULE_ID_RE_STRING: Any
MODULE_VERSION_ID_RE_STRING: Any
GCE_RESOURCE_PATH_REGEX: str
GCE_RESOURCE_NAME_REGEX: str
VPC_ACCESS_CONNECTOR_NAME_REGEX: str
ALTERNATE_HOSTNAME_SEPARATOR: str
BUILTIN_NAME_PREFIX: str
RUNTIME_RE_STRING: str
API_VERSION_RE_STRING: str
ENV_RE_STRING: str
SOURCE_LANGUAGE_RE_STRING: str
HANDLER_STATIC_FILES: str
HANDLER_STATIC_DIR: str
HANDLER_SCRIPT: str
HANDLER_API_ENDPOINT: str
LOGIN_OPTIONAL: str
LOGIN_REQUIRED: str
LOGIN_ADMIN: str
AUTH_FAIL_ACTION_REDIRECT: str
AUTH_FAIL_ACTION_UNAUTHORIZED: str
DATASTORE_ID_POLICY_LEGACY: str
DATASTORE_ID_POLICY_DEFAULT: str
SECURE_HTTP: str
SECURE_HTTPS: str
SECURE_HTTP_OR_HTTPS: str
SECURE_DEFAULT: str
REQUIRE_MATCHING_FILE: str
DEFAULT_SKIP_FILES: str
SKIP_NO_FILES: str
DEFAULT_NOBUILD_FILES: str
LOGIN: str
AUTH_FAIL_ACTION: str
SECURE: str
URL: str
POSITION: str
POSITION_HEAD: str
POSITION_TAIL: str
STATIC_FILES: str
UPLOAD: str
STATIC_DIR: str
MIME_TYPE: str
SCRIPT: str
EXPIRATION: str
API_ENDPOINT: str
HTTP_HEADERS: str
APPLICATION_READABLE: str
REDIRECT_HTTP_RESPONSE_CODE: str
APPLICATION: str
PROJECT: str
MODULE: str
SERVICE: str
AUTOMATIC_SCALING: str
MANUAL_SCALING: str
BASIC_SCALING: str
VM: str
VM_SETTINGS: str
ZONES: str
BETA_SETTINGS: str
VM_HEALTH_CHECK: str
HEALTH_CHECK: str
RESOURCES: str
LIVENESS_CHECK: str
READINESS_CHECK: str
NETWORK: str
VPC_ACCESS_CONNECTOR: str
VERSION: str
MAJOR_VERSION: str
MINOR_VERSION: str
RUNTIME: str
RUNTIME_CHANNEL: str
API_VERSION: str
MAIN: str
ENDPOINTS_API_SERVICE: str
ENV: str
ENTRYPOINT: str
RUNTIME_CONFIG: str
SOURCE_LANGUAGE: str
BUILTINS: str
INCLUDES: str
HANDLERS: str
LIBRARIES: str
DEFAULT_EXPIRATION: str
SKIP_FILES: str
NOBUILD_FILES: str
SERVICES: str
DERIVED_FILE_TYPE: str
JAVA_PRECOMPILED: str
PYTHON_PRECOMPILED: str
ADMIN_CONSOLE: str
ERROR_HANDLERS: str
BACKENDS: str
THREADSAFE: str
SERVICEACCOUNT: str
DATASTORE_AUTO_ID_POLICY: str
API_CONFIG: str
CODE_LOCK: str
ENV_VARIABLES: str
BUILD_ENV_VARIABLES: str
STANDARD_WEBSOCKET: str
APP_ENGINE_APIS: str
SOURCE_REPO_RE_STRING: str
SOURCE_REVISION_RE_STRING: str
SOURCE_REFERENCES_MAX_SIZE: int
INSTANCE_CLASS: str
MINIMUM_PENDING_LATENCY: str
MAXIMUM_PENDING_LATENCY: str
MINIMUM_IDLE_INSTANCES: str
MAXIMUM_IDLE_INSTANCES: str
MAXIMUM_CONCURRENT_REQUEST: str
MIN_NUM_INSTANCES: str
MAX_NUM_INSTANCES: str
COOL_DOWN_PERIOD_SEC: str
CPU_UTILIZATION: str
CPU_UTILIZATION_UTILIZATION: str
CPU_UTILIZATION_AGGREGATION_WINDOW_LENGTH_SEC: str
TARGET_NETWORK_SENT_BYTES_PER_SEC: str
TARGET_NETWORK_SENT_PACKETS_PER_SEC: str
TARGET_NETWORK_RECEIVED_BYTES_PER_SEC: str
TARGET_NETWORK_RECEIVED_PACKETS_PER_SEC: str
TARGET_DISK_WRITE_BYTES_PER_SEC: str
TARGET_DISK_WRITE_OPS_PER_SEC: str
TARGET_DISK_READ_BYTES_PER_SEC: str
TARGET_DISK_READ_OPS_PER_SEC: str
TARGET_REQUEST_COUNT_PER_SEC: str
TARGET_CONCURRENT_REQUESTS: str
CUSTOM_METRICS: str
METRIC_NAME: str
TARGET_TYPE: str
TARGET_TYPE_REGEX: str
CUSTOM_METRIC_UTILIZATION: str
SINGLE_INSTANCE_ASSIGNMENT: str
FILTER: str
INSTANCES: str
MAX_INSTANCES: str
IDLE_TIMEOUT: str
PAGES: str
NAME: str
ENDPOINTS_NAME: str
CONFIG_ID: str
ROLLOUT_STRATEGY: str
ROLLOUT_STRATEGY_FIXED: str
ROLLOUT_STRATEGY_MANAGED: str
TRACE_SAMPLING: str
ERROR_CODE: str
FILE: str
ON: str
ON_ALIASES: Any
OFF: str
OFF_ALIASES: Any
ENABLE_HEALTH_CHECK: str
CHECK_INTERVAL_SEC: str
TIMEOUT_SEC: str
APP_START_TIMEOUT_SEC: str
UNHEALTHY_THRESHOLD: str
HEALTHY_THRESHOLD: str
FAILURE_THRESHOLD: str
SUCCESS_THRESHOLD: str
RESTART_THRESHOLD: str
INITIAL_DELAY_SEC: str
HOST: str
PATH: str
CPU: str
MEMORY_GB: str
DISK_SIZE_GB: str
VOLUMES: str
VOLUME_NAME: str
VOLUME_TYPE: str
SIZE_GB: str
FORWARDED_PORTS: str
INSTANCE_TAG: str
NETWORK_NAME: str
SUBNETWORK_NAME: str
SESSION_AFFINITY: str
STANDARD_MIN_INSTANCES: str
STANDARD_MAX_INSTANCES: str
STANDARD_TARGET_CPU_UTILIZATION: str
STANDARD_TARGET_THROUGHPUT_UTILIZATION: str
VPC_ACCESS_CONNECTOR_NAME: str
VPC_ACCESS_CONNECTOR_EGRESS_SETTING: str
EGRESS_SETTING_ALL_TRAFFIC: str
EGRESS_SETTING_PRIVATE_RANGES_ONLY: str

class _VersionedLibrary:
    name: Any
    url: Any
    description: Any
    supported_versions: Any
    latest_version: Any
    default_version: Any
    deprecated_versions: Any
    experimental_versions: Any
    hidden_versions: Any
    def __init__(self, name, url, description, supported_versions, latest_version, default_version: Any | None = ..., deprecated_versions: Any | None = ..., experimental_versions: Any | None = ..., hidden_versions: Any | None = ...) -> None: ...
    @property
    def hidden(self): ...
    @property
    def non_deprecated_versions(self): ...

REQUIRED_LIBRARIES: Any

def GetAllRuntimes(): ...
def EnsureAsciiString(s, err): ...

class HandlerBase(validation.Validated):
    ATTRIBUTES: Any

class HttpHeadersDict(validation.ValidatedDict):
    DISALLOWED_HEADERS: Any
    MAX_HEADER_LENGTH: int
    MAX_HEADER_VALUE_LENGTHS: Any
    MAX_LEN: int
    class KeyValidator(validation.Validator):
        def Validate(self, name, unused_key: Any | None = ...): ...
    class ValueValidator(validation.Validator):
        def Validate(self, value, key: Any | None = ...): ...
        @staticmethod
        def AssertHeaderNotTooLong(name, value) -> None: ...
    KEY_VALIDATOR: Any
    VALUE_VALIDATOR: Any
    def Get(self, header_name): ...
    def __setitem__(self, key, value) -> None: ...

class URLMap(HandlerBase):
    ATTRIBUTES: Any
    COMMON_FIELDS: Any
    ALLOWED_FIELDS: Any
    def GetHandler(self): ...
    def GetHandlerType(self): ...
    def CheckInitialized(self) -> None: ...
    def AssertUniqueContentType(self) -> None: ...
    secure: Any
    def FixSecureDefaults(self) -> None: ...
    def WarnReservedURLs(self) -> None: ...
    def ErrorOnPositionForAppInfo(self) -> None: ...
    def PrettyRepr(self): ...

class AdminConsolePage(validation.Validated):
    ATTRIBUTES: Any

class AdminConsole(validation.Validated):
    ATTRIBUTES: Any
    @classmethod
    def Merge(cls, adminconsole_one, adminconsole_two): ...

class ErrorHandlers(validation.Validated):
    ATTRIBUTES: Any

class BuiltinHandler(validation.Validated):
    class DynamicAttributes(dict):
        def __init__(self, return_value, **parameters) -> None: ...
        def __contains__(self, _): ...
        def __getitem__(self, _): ...
    ATTRIBUTES: Any
    builtin_name: str
    def __init__(self, **attributes) -> None: ...
    def __setattr__(self, key, value) -> None: ...
    def __getattr__(self, key) -> None: ...
    def GetUnnormalized(self, key): ...
    def ToDict(self): ...
    @classmethod
    def IsDefined(cls, builtins_list, builtin_name): ...
    @classmethod
    def ListToTuples(cls, builtins_list): ...
    @classmethod
    def Validate(cls, builtins_list, runtime: Any | None = ...) -> None: ...

class ApiConfigHandler(HandlerBase):
    ATTRIBUTES: Any

class Library(validation.Validated):
    ATTRIBUTES: Any
    version: Any
    def CheckInitialized(self) -> None: ...

class CpuUtilization(validation.Validated):
    ATTRIBUTES: Any

class CustomMetric(validation.Validated):
    ATTRIBUTES: Any
    def CheckInitialized(self) -> None: ...

class EndpointsApiService(validation.Validated):
    ATTRIBUTES: Any
    def CheckInitialized(self) -> None: ...

class AutomaticScaling(validation.Validated):
    ATTRIBUTES: Any

class ManualScaling(validation.Validated):
    ATTRIBUTES: Any

class BasicScaling(validation.Validated):
    ATTRIBUTES: Any

class RuntimeConfig(validation.ValidatedDict):
    KEY_VALIDATOR: Any
    VALUE_VALIDATOR: Any

class VmSettings(validation.ValidatedDict):
    KEY_VALIDATOR: Any
    VALUE_VALIDATOR: Any
    @classmethod
    def Merge(cls, vm_settings_one, vm_settings_two): ...

class BetaSettings(VmSettings):
    @classmethod
    def Merge(cls, beta_settings_one, beta_settings_two): ...

class EnvironmentVariables(validation.ValidatedDict):
    KEY_VALIDATOR: Any
    VALUE_VALIDATOR: Any
    @classmethod
    def Merge(cls, env_variables_one, env_variables_two): ...

def ValidateSourceReference(ref) -> None: ...
def ValidateCombinedSourceReferencesString(source_refs) -> None: ...

class HealthCheck(validation.Validated):
    ATTRIBUTES: Any

class LivenessCheck(validation.Validated):
    ATTRIBUTES: Any

class ReadinessCheck(validation.Validated):
    ATTRIBUTES: Any

class VmHealthCheck(HealthCheck): ...

class Volume(validation.Validated):
    ATTRIBUTES: Any

class Resources(validation.Validated):
    ATTRIBUTES: Any

class Network(validation.Validated):
    ATTRIBUTES: Any

class VpcAccessConnector(validation.Validated):
    ATTRIBUTES: Any

class AppInclude(validation.Validated):
    ATTRIBUTES: Any
    @classmethod
    def MergeManualScaling(cls, appinclude_one, appinclude_two): ...
    @classmethod
    def MergeAppYamlAppInclude(cls, appyaml, appinclude): ...
    @classmethod
    def MergeAppIncludes(cls, appinclude_one, appinclude_two): ...
    @staticmethod
    def MergeSkipFiles(skip_files_one, skip_files_two): ...

class AppInfoExternal(validation.Validated):
    ATTRIBUTES: Any
    runtime: str
    def CheckInitialized(self) -> None: ...
    def GetAllLibraries(self): ...
    def GetNormalizedLibraries(self): ...
    version: Any
    def ApplyBackendSettings(self, backend_name) -> None: ...
    def GetEffectiveRuntime(self): ...
    vm_settings: Any
    def SetEffectiveRuntime(self, runtime) -> None: ...
    def NormalizeVmSettings(self) -> None: ...
    def IsVm(self): ...
    def IsThreadsafe(self): ...

def ValidateHandlers(handlers, is_include_file: bool = ...) -> None: ...
def LoadSingleAppInfo(app_info): ...

class AppInfoSummary(validation.Validated):
    ATTRIBUTES: Any

def LoadAppInclude(app_include): ...
def ParseExpiration(expiration): ...
def ValidFilename(filename): ...
