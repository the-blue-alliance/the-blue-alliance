As with any sufficiently old and complicated projects, TBA has its fair share of strange legacy code. This page tries to explain some of the weirder stuff we've had to solve over the course of the years.

## Python 3 Compatibility Shims

During the process of porting the site to Python3, there were a number of substantial changes to the App Engine runtime. Some of these necessitated implementing the legacy API on top of newer technologies to make the migration as simple as possible.

### Unit Test NDB Stub

The legacy API included an in-memory datastore stub that could be activated in unit tests. This let tests have a reproducable isolated environment where they could do reads and writes as if they were in production.

This functionality was not included in the python3 version. Instead, Google recommends to use the full datastore emulator, although there are isolation and complexity concerns for running in unit tests. We would prefer to have pure python tests.

So instead, we wrote our own in-memory datastore implementation, based on the public [RPC Spec](https://cloud.google.com/datastore/docs/reference/data/rpc/google.datastore.v1#google.datastore.v1.Datastore). During tests, we "monkey patch" this into the library's datastore interactions so we instead send requests to the local stub instead of a real datastore instance.

The stub is simplistic (it does not support all functionalities of the datastore), but it does support whatever functionality TBA uses, making it suffficient for tests.

This stub can be [found in a spearate repository](https://github.com/phil-lopreiato/google-cloud-datastore-stub) and is [published on PyPi](https://pypi.org/project/InMemoryCloudDatastoreStub/) to be included as a dependency of TBA's unit tests.

### Cross-Version CachedQueryResult

When we store raw query outputs (essentially NDB Models) in `CachedQueryResult`, they are stored in a `PickleProperty` within `CachedQueryResult`. Unfortnuately, [`pickle`](https://docs.python.org/3/library/pickle.html) compatibility between python2 and python3 is difficult to come by.

We want the two versions of the site to be totally interchangable when it comes to the data in the datastore, so we need a way to maintain backwards and forward compatibility.

There are three main points of complexity.
 - We changed the import path of models, so we'll need to rewrite those on the fly. We can do this with a custom `Unpickler` that rewrites the module paths at unpickle time. See [this answer](https://stackoverflow.com/a/40916570) for more.
 - bytestrings are handled totally differently between python 2 and 3, so we need to make sure that the py3 reader will unpickle using `encoding="bytes"`. We can do this in our custom unpickler too. Plus there's this whole thing about unpickling `datetimes`. See [this answer](https://stackoverflow.com/a/28218598).
 - Finally, there's a ndb incompatibility. The legacy app uses a [custom pickling format](https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L2964-L2970) (a serialized protobuf), which it does by defining `__getstate__` and `__setstate__` on the base `Model` class. Since the py3 compatible ndb library does not do this, unpickling them will fail. We implement these functions ourself on the `CachedModel` class (at least until this is [fixed upstream](https://github.com/googleapis/python-ndb/issues/587)) to provide compatibility. This is super complex, however, because this uses the legacy App Engine protobuf specs, which are barely documented and have minimal scaffolding available for us to build on.

### memcache APIs

The python3 runtime does not provide managed memcache, and instead recommend [migrating to Memorystore](https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/memcache-to-memorystore). To maintain application level compatibility, we implemented a wrapper around a redis client that exposes the legacy memcache interface to serve as a drop in replacement.

### Deferred/Task Queue APIs

The python3 runtime does not provide managed task queues and instead recommend [migrating to Google Cloud Tasks](https://cloud.google.com/appengine/docs/standard/python/taskqueue/push/migrating-push-queues). To maintain application level compatibility (including with the [`defer`](https://cloud.google.com/appengine/docs/standard/python/taskqueue/push/creating-tasks#using_the_instead_of_a_worker_service) API), we implemented a wrapper to maintain the same interface, but instead backed by the new technology