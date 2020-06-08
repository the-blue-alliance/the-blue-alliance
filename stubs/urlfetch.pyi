from typing import Any, Optional

unicode = str
basestring = basestring
unicode = unicode

class UrlfetchException(IOError): ...
class ContentLimitExceeded(UrlfetchException): ...
class URLError(UrlfetchException, ValueError): ...
class ContentDecodingError(UrlfetchException): ...
class TooManyRedirects(UrlfetchException): ...
class Timeout(UrlfetchException): ...

class cached_property:
    __doc__: Any = ...
    __name__: Any = ...
    __module__: Any = ...
    def __init__(self, fget: Optional[Any] = ..., fset: Optional[Any] = ..., fdel: Optional[Any] = ..., doc: Optional[Any] = ...) -> None: ...
    def __get__(self, instance: Any, owner: Any): ...
    def __set__(self, instance: Any, value: Any): ...
    def __delete__(self, instance: Any): ...
    def setter(self, fset: Any): ...
    def deleter(self, fdel: Any): ...

class Response:
    msg: Any = ...
    status: Any = ...
    status_code: Any = ...
    reason: Any = ...
    version: Any = ...
    total_time: Any = ...
    getheader: Any = ...
    getheaders: Any = ...
    length_limit: Any = ...
    def __init__(self, r: Any, **kwargs: Any) -> None: ...
    def read(self, chunk_size: int = ...): ...
    def __iter__(self) -> Any: ...
    def __next__(self): ...
    next: Any = ...
    def __enter__(self): ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any): ...
    @classmethod
    def from_httplib(cls, connection: Any, **kwargs: Any): ...
    def body(self): ...
    @property
    def content(self): ...
    def text(self): ...
    def json(self): ...
    def headers(self): ...
    def cookies(self): ...
    def cookiestring(self): ...
    def links(self): ...
    def close(self) -> None: ...
    def __del__(self) -> None: ...

class Session:
    headers: Any = ...
    cookies: Any = ...
    def __init__(self, headers: Any = ..., cookies: Any = ..., auth: Optional[Any] = ...) -> None: ...
    def putheader(self, header: Any, value: Any) -> None: ...
    def popheader(self, header: Any): ...
    def putcookie(self, key: Any, value: str = ...) -> None: ...
    def popcookie(self, key: Any): ...
    @property
    def cookiestring(self): ...
    @cookiestring.setter
    def cookiestring(self, value: Any) -> None: ...
    def snapshot(self): ...
    def request(self, *args: Any, **kwargs: Any): ...
    def fetch(self, *args: Any, **kwargs: Any): ...
    def get(self, *args: Any, **kwargs: Any): ...
    def post(self, *args: Any, **kwargs: Any): ...
    def put(self, *args: Any, **kwargs: Any): ...
    def delete(self, *args: Any, **kwargs: Any): ...
    def head(self, *args: Any, **kwargs: Any): ...
    def options(self, *args: Any, **kwargs: Any): ...
    def trace(self, *args: Any, **kwargs: Any): ...
    def patch(self, *args: Any, **kwargs: Any): ...

def fetch(*args: Any, **kwargs: Any): ...
def request(url: Any, method: str = ..., params: Optional[Any] = ..., data: Optional[Any] = ..., headers: Any = ..., timeout: Optional[Any] = ..., files: Any = ..., randua: bool = ..., auth: Optional[Any] = ..., length_limit: Optional[Any] = ..., proxies: Optional[Any] = ..., trust_env: bool = ..., max_redirects: int = ..., source_address: Optional[Any] = ..., validate_certificate: Optional[Any] = ..., **kwargs: Any): ...

get: Any
post: Any
put: Any
delete: Any
head: Any
options: Any
trace: Any
patch: Any

class ObjectDict(dict):
    def __getattr__(self, name: Any): ...
    def __setattr__(self, name: Any, value: Any) -> None: ...
