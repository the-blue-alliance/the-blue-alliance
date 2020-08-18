import firebase_admin


def app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except Exception:
        return firebase_admin.initialize_app()
