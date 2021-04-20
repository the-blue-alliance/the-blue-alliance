The currently logged in user can be obtained via the [`current_user` method](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/auth.py) and returns a [`User`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/models/user.py) object. The `current_user` method will inspect the encrypted [`session`](https://flask.palletsprojects.com/en/1.1.x/api/#sessions) object stored in cookies and verify the `session` object is still valid. The `User` object is a wrapper around fetching an [`Account`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/auth.py) + related models for a given Firebase session object.

The `current_user` method should **NOT** be used in services that cannot be accessed via a browser where a session cookie will not be available. The currently authenticated user should be fetched in a different way, being careful to ensure proper ownership.

```python
from backend.common.auth import current_user

def route() -> str:
    user = current_user()
    if user:
      # User is logged in!
    else:
      # User is not signed in, or user's session has expired
```
