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

### First time local setup

If you want to test myTBA (or other sign-in related features) locally, you'll need to provide a couple of Firebase secrets in order for the initialization sequence to succeed.

1. Go to https://console.firebase.google.com/
2. Create project
3. Enter a project name, such as `tba-dev`
4. Disable Google Analytics, hit Create Project
5. Go to Project Settings
6. Create a web platform App
7. Enter a name, such as `tba-dev`
8. Hit Register app
9. Copy the `appId` and `authDomain` to `src/backend/web/static/javascript/tba_js/tba_keys.js`. You may need to `chmod` this depending on your local environment and how the file was made.
10. Run `./ops/build/run_buildweb.sh` to rebuild JS bundles.
11. Go to http://localhost:8080/account/login and Sign in with Google.

Nothing actually gets used in your Firebase project, so you won't be charged for anything. TBA uses the Firebase emulator to provide two fake accounts (see below) - however in order to connect to the emulator, auth initialization must succeed, and in order for that to succeed, it must have a valid app ID and auth domain.

### Firebase Auth Emulator

By default, the development container will run using the Firebase auth emulator (generally available at [localhost:4000/auth](http://localhost:4000/auth). If you're using a [`google_application_credentials` key](https://github.com/the-blue-alliance/the-blue-alliance/wiki/GAE-Firebase-Setup#setup-google-service-account-keys) locally and would like to hit an upstream Firebase project for authentication, set the `auth_use_prod` option in [[tba_dev_config.json|tba_dev_config]] to `true`.

By default, the Firebase auth emulator should come with two accounts - an admin account, and a non-admin (user) account. These accounts should be inserted after starting the development container. If they fail to create, need to be re-created, or the emulator is running in a different context, the accounts can be re-created by running the `create_auth_emulator_accounts.py` script.

```bash
$ python ops/dev/vagrant/create_auth_emulator_accounts.py --project=your-project-id
```
