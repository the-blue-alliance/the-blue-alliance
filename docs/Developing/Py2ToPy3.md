# Py 2 -> Py 3 Migration Notes

## Move `old_py2/` files
Migrated files should be **moved** from the `old_py2/` folder to the new destination in order to [preserve git blame history](https://github.com/the-blue-alliance/the-blue-alliance/blame/py3/src/backend/common/models/sitevar.py). After moving, edits can be made to the file to update it for the Python 3 migration.

## Remove google.appengine imports
Any `google.appengine` namespaced imports should be replaced with their new Google Cloud libraries.

```
google.appengine.api.app_identity => backend.common.environment(ish)
google.appengine.api.memcache => (TODO: Move)
google.appengine.api.search => (TODO: Move)
google.appengine.api.taskqueue => google.cloud.tasks_v2
google.appengine.api.urlfetch => requests
google.appengine.api.users => backend.common.auth

google.appengine.ext.ndb => google.cloud.ndb
google.appengine.ext.deferred => backend.common.deferred
google.appengine.ext.testbed => (Removed)
```

## Create Sitevar wrapper for Sitevars
Code using `Sitevar` directly should be removed in favor of a [typed `Sitevar` wrapper](https://github.com/the-blue-alliance/the-blue-alliance/tree/py3/src/backend/common/sitevars) in `commom/sitevars`.  This will allow us to define specific, type-safe APIs around sitevars, along with providing default values for sitevars that do not exist in a new instance.

## Google Analytics Event Tracking
Calls to the `google-analytics.com/collect` endpoint are now wrapped via [`GoogleAnalytics.track_event`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/google_analytics.py).

## Updating Tests

### Remove use of `unittest`

`unittest` is no longer used for running our tests. This means removing the use of `unittest2.TestCase` classes, along with any `test_` methods that take `self` as an argument.

### Update asserts

The old `self.assertEqual` style asserts are no longer used. Use the `assert` keyword instead.

```
self.assertEqual(one, two) => assert one == two
self.assertTrue(obj) => assert obj
self.assertFalse(obj) => assert not obj
self.assertIsNone(obj) => assert obj is None
self.assertIsNotNone(obj) => assert obj is not None
```

When updating tests, note [when to use `is` vs when to use `==`](https://stackoverflow.com/a/15008404/537341).
