# Py 2 -> Py 3 Migration Notes

## Remove google.appengine imports
Any `google.appengine` namespaced imports should be replaced with their new Google Cloud libraries.

```
google.appengine.api.app_identity => (TODO: Move)
google.appengine.api.memcache => (TODO: Move)
google.appengine.api.search => (TODO: Move)
google.appengine.api.taskqueue => (TODO: Move)
google.appengine.api.urlfetch => urlfetch
google.appengine.api.users => (TODO: Move)

google.appengine.ext.ndb => google.cloud.ndb
google.appengine.ext.deferred => (TODO: Move)
google.appengine.ext.testbed => (Removed)
```

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
