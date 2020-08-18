import enum

from dataclasses import dataclass
from typing import Dict


@enum.unique
class AccountPermission(enum.IntEnum):
    """
    Permissions available for Accounts (see Account.permissions)
    """

    REVIEW_MEDIA = 1
    REVIEW_OFFSEASON_EVENTS = 2
    REVIEW_APIWRITE = 3
    REVIEW_DESIGNS = 4
    REVIEW_EVENT_MEDIA = 5
    OFFSEASON_EVENTWIZARD = 6


@dataclass
class PermissionDescription:
    name: str
    description: str


PERMISSIONS: Dict[AccountPermission, PermissionDescription] = {
    AccountPermission.REVIEW_MEDIA: PermissionDescription(
        "REVIEW_MEDIA", "Can review (accept/reject) media suggestions"
    ),
    AccountPermission.REVIEW_OFFSEASON_EVENTS: PermissionDescription(
        "REVIEW_OFFSEASON_EVENTS",
        "Can accept and create offseason events from suggestions",
    ),
    AccountPermission.REVIEW_APIWRITE: PermissionDescription(
        "REVIEW_APIWRITE", "Can review and grant requests for trusted API tokens"
    ),
    AccountPermission.REVIEW_DESIGNS: PermissionDescription(
        "REVIEW_DESIGNS",
        "Can link CAD models and Behind the Design blog posts to team robot profiles",
    ),
    AccountPermission.REVIEW_EVENT_MEDIA: PermissionDescription(
        "REVIEW_EVENT_MEDIA", "Can approve media (non-match video) linked to events"
    ),
    AccountPermission.OFFSEASON_EVENTWIZARD: PermissionDescription(
        "OFFSEASON_EVENTWIZARD", "Can use the eventwizard for any offseason event"
    ),
}
