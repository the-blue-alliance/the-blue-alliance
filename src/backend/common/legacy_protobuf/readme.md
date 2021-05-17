# Legacy GAE Protobuf Compatibility

This directory contains a reimplementation of some functions from the original legacy runtime. This is necessary because there are places we store serialized models to disk (sepcifically, within `CachedQueryResult`), and the legacy NDB library's serialization protocol used this format.

This happened because `ndb.Model` defined `__getstate__` and `__setstate__` in the legacy app to define a [custom pickling format](https://docs.python.org/3/library/pickle.html#pickle-state), but not in the new Google Cloud NDB Library. In the legacy implementation, we'd return a serialized protobuf, whose format was tied to the legacy runtime.

In order to maintain compatibility with the legacy app, we've reimplemented the serialiation/deserialization. For deserialiation only, we can rely partially on private functions of the Cloud NDB library (and trust that our unit tests will catch future breakages). We've implemented these pickle state hooks on `CachedModel`, which is the base class we require things used in cached queries to inherit from.

This gap in compatibility is [tracked in an upstream issue](https://github.com/googleapis/python-ndb/issues/587), whose resolution will let us remove much of this code.
