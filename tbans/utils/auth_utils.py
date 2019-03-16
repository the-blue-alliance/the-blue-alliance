from google.appengine.api.app_identity import app_identity


def get_firebase_messaging_access_token():
    """ Get a access token for the application with the Firebase messaging scope.

    Returns:
        access_token (string): Bearer token used to authenticate requests.
    """
    access_token, _ = app_identity.get_access_token('https://www.googleapis.com/auth/firebase.messaging')
    return access_token
