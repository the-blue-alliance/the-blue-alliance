from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    FIREBASE_SECRET: str


class FirebaseSecrets(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "firebase.secrets"

    @staticmethod
    def description() -> str:
        return "Firebase Push Notifications"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(FIREBASE_SECRET="")
