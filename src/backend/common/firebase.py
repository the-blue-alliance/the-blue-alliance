import firebase_admin

from backend.common.environment import Environment


def app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except Exception:
        project = Environment.project()
        return firebase_admin.initialize_app(options={"projectId": project})
