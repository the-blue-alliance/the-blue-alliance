import datetime
import six
from google.cloud.ndb import exceptions, key as key_module
from typing import Any, Optional

Key = key_module.Key
BlobKey: Any
GeoPt: Any
Rollback = exceptions.Rollback

class KindError(exceptions.BadValueError): ...
class InvalidPropertyError(exceptions.Error): ...
BadProjectionError = InvalidPropertyError

class UnprojectedPropertyError(exceptions.Error): ...
class ReadonlyPropertyError(exceptions.Error): ...
class ComputedPropertyError(ReadonlyPropertyError): ...
class UserNotFoundError(exceptions.Error): ...

class _NotEqualMixin:
    def __ne__(self, other: Any) -> Any: ...

class IndexProperty(_NotEqualMixin):
    def __new__(cls, name: Any, direction: Any): ...
    @property
    def name(self): ...
    @property
    def direction(self): ...
    def __eq__(self, other: Any) -> Any: ...
    def __hash__(self) -> Any: ...

class Index(_NotEqualMixin):
    def __new__(cls, kind: Any, properties: Any, ancestor: Any): ...
    @property
    def kind(self): ...
    @property
    def properties(self): ...
    @property
    def ancestor(self): ...
    def __eq__(self, other: Any) -> Any: ...
    def __hash__(self) -> Any: ...

class IndexState(_NotEqualMixin):
    def __new__(cls, definition: Any, state: Any, id: Any): ...
    @property
    def definition(self): ...
    @property
    def state(self): ...
    @property
    def id(self): ...
    def __eq__(self, other: Any) -> Any: ...
    def __hash__(self) -> Any: ...

class ModelAdapter:
    def __new__(self, *args: Any, **kwargs: Any) -> None: ...

def make_connection(*args: Any, **kwargs: Any) -> None: ...

class ModelAttribute: ...

class _BaseValue(_NotEqualMixin):
    b_val: Any = ...
    def __init__(self, b_val: Any) -> None: ...
    def __eq__(self, other: Any) -> Any: ...
    def __hash__(self) -> Any: ...

class Property(ModelAttribute):
    def __init__(self, name: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...
    def __eq__(self, value: Any) -> Any: ...
    def __ne__(self, value: Any) -> Any: ...
    def __lt__(self, value: Any) -> Any: ...
    def __le__(self, value: Any) -> Any: ...
    def __gt__(self, value: Any) -> Any: ...
    def __ge__(self, value: Any) -> Any: ...
    IN: Any = ...
    def __neg__(self): ...
    def __pos__(self): ...
    def __get__(self, entity: Any, unused_cls: Optional[Any] = ...): ...
    def __set__(self, entity: Any, value: Any) -> None: ...
    def __delete__(self, entity: Any) -> None: ...

class ModelKey(Property):
    def __init__(self) -> None: ...

class BooleanProperty(Property, bool): ...
class IntegerProperty(Property, int): ...
class FloatProperty(Property, float): ...

class _CompressedValue(six.binary_type):
    z_val: Any = ...
    def __init__(self, z_val: Any) -> None: ...
    def __eq__(self, other: Any) -> Any: ...
    def __hash__(self) -> Any: ...

class BlobProperty(Property):
    def __init__(self, name: Optional[Any] = ..., compressed: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...

class CompressedTextProperty(BlobProperty):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class TextProperty(Property, str):
    def __new__(cls, *args: Any, **kwargs: Any): ...
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class StringProperty(TextProperty, str):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class GeoPtProperty(Property): ...
class PickleProperty(BlobProperty): ...

class JsonProperty(BlobProperty, dict, list):
    def __init__(self, name: Optional[Any] = ..., compressed: Optional[Any] = ..., json_type: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...

class User:
    def __init__(self, email: Optional[Any] = ..., _auth_domain: Optional[Any] = ..., _user_id: Optional[Any] = ...) -> None: ...
    def nickname(self): ...
    def email(self): ...
    def user_id(self): ...
    def auth_domain(self): ...
    def __hash__(self) -> Any: ...
    def __eq__(self, other: Any) -> Any: ...
    def __lt__(self, other: Any) -> Any: ...

class UserProperty(Property):
    def __init__(self, name: Optional[Any] = ..., auto_current_user: Optional[Any] = ..., auto_current_user_add: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...

class KeyProperty(Property, Key):
    def __init__(self, name: Optional[Any] = ..., kind: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...

class BlobKeyProperty(Property): ...

class DateTimeProperty(Property, datetime.datetime):
    def __init__(self, name: Optional[Any] = ..., auto_now: Optional[Any] = ..., auto_now_add: Optional[Any] = ..., tzinfo: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., required: Optional[Any] = ..., default: Optional[Any] = ..., choices: Optional[Any] = ..., validator: Optional[Any] = ..., verbose_name: Optional[Any] = ..., write_empty_list: Optional[Any] = ...) -> None: ...

class DateProperty(DateTimeProperty): ...
class TimeProperty(DateTimeProperty): ...

class StructuredProperty(Property):
    def __init__(self, model_class: Any, name: Optional[Any] = ..., **kwargs: Any) -> None: ...
    def __getattr__(self, attrname: Any): ...
    IN: Any = ...

class LocalStructuredProperty(BlobProperty):
    def __init__(self, model_class: Any, **kwargs: Any) -> None: ...

class GenericProperty(Property):
    def __init__(self, name: Optional[Any] = ..., compressed: bool = ..., **kwargs: Any) -> None: ...

class ComputedProperty(GenericProperty):
    def __init__(self, func: Any, name: Optional[Any] = ..., indexed: Optional[Any] = ..., repeated: Optional[Any] = ..., verbose_name: Optional[Any] = ...) -> None: ...

class MetaModel(type):
    def __init__(cls, name: Any, bases: Any, classdict: Any) -> None: ...

class Model(_NotEqualMixin, metaclass=MetaModel):
    key: Any = ...
    def __init__(_self: Any, **kwargs: Any) -> None: ...
    def __hash__(self) -> Any: ...
    def __eq__(self, other: Any) -> Any: ...
    def __lt__(self, value: Any) -> Any: ...
    def __le__(self, value: Any) -> Any: ...
    def __gt__(self, value: Any) -> Any: ...
    def __ge__(self, value: Any) -> Any: ...
    gql: Any = ...
    put: Any = ...
    put_async: Any = ...
    query: Any = ...
    allocate_ids: Any = ...
    allocate_ids_async: Any = ...
    get_by_id: Any = ...
    get_by_id_async: Any = ...
    get_or_insert: Any = ...
    get_or_insert_async: Any = ...
    populate: Any = ...
    has_complete_key: Any = ...
    to_dict: Any = ...

class Expando(Model):
    def __getattr__(self, name: Any): ...
    def __setattr__(self, name: Any, value: Any): ...
    def __delattr__(self, name: Any): ...

def get_multi_async(keys: Any, read_consistency: Optional[Any] = ..., read_policy: Optional[Any] = ..., transaction: Optional[Any] = ..., retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def get_multi(keys: Any, read_consistency: Optional[Any] = ..., read_policy: Optional[Any] = ..., transaction: Optional[Any] = ..., retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def put_multi_async(entities: Any, retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def put_multi(entities: Any, retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def delete_multi_async(keys: Any, retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def delete_multi(keys: Any, retries: Optional[Any] = ..., timeout: Optional[Any] = ..., deadline: Optional[Any] = ..., use_cache: Optional[Any] = ..., use_global_cache: Optional[Any] = ..., global_cache_timeout: Optional[Any] = ..., use_datastore: Optional[Any] = ..., use_memcache: Optional[Any] = ..., memcache_timeout: Optional[Any] = ..., max_memcache_items: Optional[Any] = ..., force_writes: Optional[Any] = ..., _options: Optional[Any] = ...): ...
def get_indexes_async(**options: Any) -> None: ...
def get_indexes(**options: Any) -> None: ...
