from typing import TYPE_CHECKING

from backend.common.environment import Environment

if TYPE_CHECKING:
    import firebase_admin


def app() -> "firebase_admin.App":
    import firebase_admin

    try:
        return firebase_admin.get_app()
    except Exception:
        project = Environment.project()
        return firebase_admin.initialize_app(options={"projectId": project})
