from google.appengine.api import api_base_pb2 as api_base_pb2, apiproxy_stub_map as apiproxy_stub_map, cmp_compat as cmp_compat, datastore_admin as datastore_admin, datastore_errors as datastore_errors, datastore_types as datastore_types, yaml_errors as yaml_errors
from google.appengine.datastore import datastore_index as datastore_index, datastore_pb as datastore_pb, datastore_pbs as datastore_pbs, datastore_query as datastore_query, datastore_stub_index as datastore_stub_index, datastore_v4_pb2 as datastore_v4_pb2
from google.appengine.datastore.datastore_pbs import googledatastore as googledatastore
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from google.protobuf import message as message
from typing import Any

long = int
MINIMUM_VERSION: int
SEQUENTIAL: str
SCATTERED: str
logger: Any

def GetInvisibleSpecialPropertyNames(): ...
def PrepareSpecialPropertiesForStore(entity_proto) -> None: ...
def LoadEntity(entity, keys_only: bool = ..., property_names: Any | None = ...): ...
def LoadRecord(record, keys_only: bool = ..., property_names: Any | None = ...): ...
def StoreRecord(record): ...
def PrepareSpecialPropertiesForLoad(entity_proto) -> None: ...
def Check(test, msg: str = ..., error_code=...) -> None: ...
def CheckValidUTF8(string, desc): ...
def CheckAppId(request_trusted, request_app_id, app_id) -> None: ...
def CheckReference(request_trusted, request_app_id, key, require_id_or_name: bool = ...) -> None: ...
def CheckEntity(request_trusted, request_app_id, entity) -> None: ...
def CheckProperty(request_trusted, request_app_id, prop, indexed: bool = ...) -> None: ...
def CheckPropertyValue(name, value, max_length, meaning) -> None: ...
def CheckTransaction(request_trusted, request_app_id, transaction) -> None: ...
def CheckQuery(query, filters, orders, max_query_components) -> None: ...

class ValueRange:
    def __init__(self) -> None: ...
    def Update(self, rel_op, limit) -> None: ...
    def Contains(self, value): ...
    def Remap(self, mapper) -> None: ...
    def MapExtremes(self, mapper): ...

def ParseKeyFilteredQuery(filters, orders): ...
def ParseKindQuery(query, filters, orders): ...
def ParseNamespaceQuery(query, filters, orders): ...
def ParsePropertyQuery(query, filters, orders): ...
def SynthesizeUserId(email): ...
def FillUsersInQuery(filters) -> None: ...
def FillUser(property) -> None: ...

class BaseCursor:
    keys_only: Any
    property_names: Any
    group_by: Any
    app: Any
    cursor: Any
    def __init__(self, query, dsquery, orders, index_list) -> None: ...
    def PopulateQueryResult(self, result, count, deprecated_offset, compile: bool = ..., first_result: bool = ...) -> None: ...

class ListCursor(BaseCursor):
    def __init__(self, query, dsquery, orders, index_list, results) -> None: ...

class LiveTxn:
    ACTIVE: int
    COMMITTED: int
    ROLLEDBACK: int
    FAILED: int
    def __init__(self, txn_manager, app, allow_multiple_eg, mode) -> None: ...
    def Get(self, reference): ...
    def GetQueryCursor(self, query, filters, orders, index_list): ...
    def Put(self, entity, insert, indexes) -> None: ...
    def Delete(self, reference, indexes) -> None: ...
    def AddActions(self, actions, max_actions: Any | None = ...) -> None: ...
    def Rollback(self) -> None: ...
    def Commit(self): ...
    def GetMutationVersion(self, reference): ...

class EntityRecord:
    entity: Any
    metadata: Any
    def __init__(self, entity, metadata: Any | None = ...) -> None: ...

class EntityGroupTracker:
    APPLIED: int
    def __init__(self, entity_group) -> None: ...

class EntityGroupMetaData:
    def __init__(self, entity_group) -> None: ...
    def CatchUp(self) -> None: ...
    def Log(self, txn) -> None: ...
    def Unlog(self, txn) -> None: ...
    def __eq__(self, other): ...
    def __lt__(self, other): ...

class BaseConsistencyPolicy: ...
class MasterSlaveConsistencyPolicy(BaseConsistencyPolicy): ...
class BaseHighReplicationConsistencyPolicy(BaseConsistencyPolicy): ...

class TimeBasedHRConsistencyPolicy(BaseHighReplicationConsistencyPolicy):
    def SetClassificationMap(self, classification_map) -> None: ...

class PseudoRandomHRConsistencyPolicy(BaseHighReplicationConsistencyPolicy):
    is_using_cloud_datastore_emulator: bool
    emulator_port: Any
    def __init__(self, probability: Any | None = ..., seed: int = ...) -> None: ...
    def SetProbability(self, probability) -> None: ...
    def SetSeed(self, seed) -> None: ...
    @property
    def probability(self): ...
    @property
    def random_seed(self): ...

class BaseTransactionManager:
    def __init__(self, consistency_policy: Any | None = ...) -> None: ...
    def SetConsistencyPolicy(self, policy) -> None: ...
    def Clear(self) -> None: ...
    def BeginTransaction(self, app, allow_multiple_eg, previous_transaction: Any | None = ..., mode=...): ...
    def GetTxn(self, transaction, request_trusted, request_app): ...
    def Groom(self) -> None: ...
    def Flush(self) -> None: ...

class BaseIndexManager:
    WRITE_ONLY: Any
    READ_WRITE: Any
    DELETED: Any
    ERROR: Any
    def __init__(self) -> None: ...
    def CreateIndex(self, index, trusted: bool = ..., calling_app: Any | None = ...): ...
    def GetIndexes(self, app, trusted: bool = ..., calling_app: Any | None = ...): ...
    def UpdateIndex(self, index, trusted: bool = ..., calling_app: Any | None = ...) -> None: ...
    def DeleteIndex(self, index, trusted: bool = ..., calling_app: Any | None = ...) -> None: ...

class BaseDatastore(BaseTransactionManager, BaseIndexManager):
    def __init__(self, require_indexes: bool = ..., consistency_policy: Any | None = ..., use_atexit: bool = ..., auto_id_policy=...) -> None: ...
    def Clear(self) -> None: ...
    def GetQueryCursor(self, raw_query, trusted: bool = ..., calling_app: Any | None = ...): ...
    def Get(self, raw_keys, transaction: Any | None = ..., eventual_consistency: bool = ..., trusted: bool = ..., calling_app: Any | None = ...): ...
    def Put(self, raw_entities, cost, transaction: Any | None = ..., trusted: bool = ..., calling_app: Any | None = ...): ...
    def Delete(self, raw_keys, cost, transaction: Any | None = ..., trusted: bool = ..., calling_app: Any | None = ...): ...
    def Touch(self, raw_keys, trusted: bool = ..., calling_app: Any | None = ...) -> None: ...
    def SetAutoIdPolicy(self, auto_id_policy) -> None: ...
    def Write(self) -> None: ...
    def Close(self) -> None: ...

class EntityGroupPseudoKind:
    name: str
    base_version: Any
    def Get(self, txn, key): ...
    def Query(self, query, filters, orders) -> None: ...

class _CachedIndexDefinitions:
    file_names: Any
    last_modifieds: Any
    index_protos: Any
    def __init__(self, file_names, last_modifieds, index_protos) -> None: ...

class DatastoreStub:
    def __init__(self, datastore, app_id: Any | None = ..., trusted: Any | None = ..., root_path: Any | None = ...) -> None: ...
    def Clear(self) -> None: ...
    def QueryHistory(self): ...
    def SetTrusted(self, trusted) -> None: ...

class StubQueryConverter(datastore_pbs._QueryConverter):
    def __init__(self, entity_converter) -> None: ...
    def v4_to_v3_compiled_cursor(self, v4_cursor, v3_compiled_cursor) -> None: ...
    def v3_to_v4_compiled_cursor(self, v3_compiled_cursor): ...
    def v4_to_v3_query(self, v4_partition_id, v4_query, v3_query) -> None: ...
    def v3_to_v4_query(self, v3_query, v4_query) -> None: ...
    def v1_to_v3_compiled_cursor(self, v1_cursor, v3_compiled_cursor) -> None: ...
    def v3_to_v1_compiled_cursor(self, v3_compiled_cursor): ...
    def v1_to_v3_query(self, v1_partition_id, v1_query, v3_query) -> None: ...
    def v3_to_v1_query(self, v3_query, v1_query) -> None: ...

def get_query_converter(id_resolver: Any | None = ...): ...

class StubServiceConverter:
    def __init__(self, entity_converter, query_converter) -> None: ...
    def v1_to_v3_cursor(self, v1_query_handle, v3_cursor): ...
    def v1_to_v3_txn(self, v1_txn, v3_txn): ...
    def v1_to_v3_begin_transaction_req(self, app_id, v1_req): ...
    def v3_to_v1_begin_transaction_resp(self, v3_resp): ...
    def v1_rollback_req_to_v3_txn(self, v1_req): ...
    def v1_commit_req_to_v3_txn(self, v1_req): ...
    def v1_run_query_req_to_v3_query(self, v1_req, new_txn: Any | None = ...): ...
    def v3_to_v1_run_query_req(self, v3_req): ...
    def v1_run_query_resp_to_v3_query_result(self, v1_resp): ...
    def v3_to_v1_run_query_resp(self, v3_resp, new_txn: Any | None = ...): ...
    def v1_to_v3_get_req(self, v1_req, new_txn: Any | None = ...): ...
    def v3_to_v1_lookup_resp(self, v3_resp, new_txn: Any | None = ...): ...
    def v1_to_v3_query_result(self, v1_batch): ...
    def v3_to_v1_query_result_batch(self, v3_result, v1_batch) -> None: ...
    def v4_to_v3_cursor(self, v4_query_handle, v3_cursor): ...
    def v4_to_v3_txn(self, v4_txn, v3_txn): ...
    def v4_to_v3_begin_transaction_req(self, app_id, v4_req): ...
    def v3_to_v4_begin_transaction_resp(self, v3_resp): ...
    def v4_rollback_req_to_v3_txn(self, v4_req): ...
    def v4_commit_req_to_v3_txn(self, v4_req): ...
    def v4_run_query_req_to_v3_query(self, v4_req): ...
    def v3_to_v4_run_query_req(self, v3_req): ...
    def v4_run_query_resp_to_v3_query_result(self, v4_resp): ...
    def v3_to_v4_run_query_resp(self, v3_resp): ...
    def v4_to_v3_next_req(self, v4_req): ...
    def v3_to_v4_continue_query_resp(self, v3_resp): ...
    def v4_to_v3_get_req(self, v4_req): ...
    def v3_to_v4_lookup_resp(self, v3_resp): ...
    def v4_to_v3_query_result(self, v4_batch): ...
    def v3_to_v4_query_result_batch(self, v3_result, v4_batch) -> None: ...

def get_service_converter(id_resolver: Any | None = ...): ...
def ReverseBitsInt64(v): ...
def ToScatteredId(v): ...
def IdToCounter(k): ...
def CompareEntityPbByKey(a, b): ...
def NormalizeCursors(query, first_sort_direction) -> None: ...
def UpdateEmulatorConfig(port, auto_id_policy: Any | None = ..., consistency_policy: Any | None = ...) -> None: ...
