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

### Firebase Auth Emulator

By default, the development container will run using the Firebase auth emulator (generally available at [localhost:4000/auth](http://localhost:4000/auth). If you're using a [`google_application_credentials` key](https://github.com/the-blue-alliance/the-blue-alliance/wiki/GAE-Firebase-Setup#setup-google-service-account-keys) locally and would like to hit an upstream Firebase project for authentication, set the `auth_use_prod` option in [[tba_dev_config.json|tba_dev_config]] to `true`.

By default, the Firebase auth emulator should come with two accounts - an admin account, and a non-admin (user) account. These accounts should be inserted after starting the development container. If they fail to create, need to be re-created, or the emulator is running in a different context, the accounts can be re-created by running the `create_auth_emulator_accounts.py` script.

```bash
$ python ops/dev/vagrant/create_auth_emulator_accounts.py --project=your-project-id
```
