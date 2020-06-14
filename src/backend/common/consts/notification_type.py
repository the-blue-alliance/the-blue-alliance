import enum
from typing import Dict, Set


@enum.unique
class NotificationType(enum.IntEnum):
    """
    Constants regarding the different types of notification we can send to a device

    See https://docs.google.com/document/d/1SV-hNCtgAn2hSMZaC973UdLHCFXCNpvq_RKq0UoY4yg/edit#
    """

    # DO NOT CHANGE THESE CONSTANTS
    UPCOMING_MATCH = 0
    MATCH_SCORE = 1
    LEVEL_STARTING = 2
    ALLIANCE_SELECTION = 3
    AWARDS = 4
    MEDIA_POSTED = 5
    DISTRICT_POINTS_UPDATED = 6
    SCHEDULE_UPDATED = 7
    FINAL_RESULTS = 8
    PING = 9  # This type of message is sent when the user hits 'ping device' in their account overview
    BROADCAST = 10  # Gives functionality for admins to send to many devices
    MATCH_VIDEO = 11
    EVENT_MATCH_VIDEO = 12  # Not user exposed

    # These aren't notifications, but used for upstream API calls
    UPDATE_FAVORITES = 100
    UPDATE_SUBSCRIPTIONS = 101

    # This is used for verification that the proper people are in control
    VERIFICATION = 200


TYPE_NAMES: Dict[NotificationType, str] = {
    NotificationType.UPCOMING_MATCH: "upcoming_match",
    NotificationType.MATCH_SCORE: "match_score",
    NotificationType.LEVEL_STARTING: "starting_comp_level",
    NotificationType.ALLIANCE_SELECTION: "alliance_selection",
    NotificationType.AWARDS: "awards_posted",
    NotificationType.MEDIA_POSTED: "media_posted",
    NotificationType.DISTRICT_POINTS_UPDATED: "district_points_updated",
    NotificationType.SCHEDULE_UPDATED: "schedule_updated",
    NotificationType.FINAL_RESULTS: "final_results",
    NotificationType.PING: "ping",
    NotificationType.BROADCAST: "broadcast",
    NotificationType.MATCH_VIDEO: "match_video",
    NotificationType.EVENT_MATCH_VIDEO: "event_match_video",
    NotificationType.UPDATE_FAVORITES: "update_favorites",
    NotificationType.UPDATE_SUBSCRIPTIONS: "update_subscriptions",
    NotificationType.VERIFICATION: "verification",
}


RENDER_NAMES: Dict[NotificationType, str] = {
    NotificationType.UPCOMING_MATCH: "Upcoming Match",
    NotificationType.MATCH_SCORE: "Match Score",
    NotificationType.LEVEL_STARTING: "Competition Level Starting",
    NotificationType.ALLIANCE_SELECTION: "Alliance Selection",
    NotificationType.AWARDS: "Awards Posted",
    NotificationType.MEDIA_POSTED: "Media Posted",
    NotificationType.DISTRICT_POINTS_UPDATED: "District Points Updated",
    NotificationType.SCHEDULE_UPDATED: "Event Schedule Updated",
    NotificationType.FINAL_RESULTS: "Final Results",
    NotificationType.MATCH_VIDEO: "Match Video Added",
    NotificationType.EVENT_MATCH_VIDEO: "Match Video Added",
}


TYPES: Dict[str, NotificationType] = {
    "upcoming_match": NotificationType.UPCOMING_MATCH,
    "match_score": NotificationType.MATCH_SCORE,
    "starting_comp_level": NotificationType.LEVEL_STARTING,
    "alliance_selection": NotificationType.ALLIANCE_SELECTION,
    "awards_posted": NotificationType.AWARDS,
    "media_posted": NotificationType.MEDIA_POSTED,
    "district_points_updated": NotificationType.DISTRICT_POINTS_UPDATED,
    "schedule_updated": NotificationType.SCHEDULE_UPDATED,
    "final_results": NotificationType.FINAL_RESULTS,
    "match_video": NotificationType.MATCH_VIDEO,
    "event_match_video": NotificationType.EVENT_MATCH_VIDEO,
    "update_favorites": NotificationType.UPDATE_FAVORITES,
    "update_subscriptions": NotificationType.UPDATE_SUBSCRIPTIONS,
    "verification": NotificationType.VERIFICATION,
}


ENABLED_NOTIFICATIONS: Dict[NotificationType, str] = {
    NotificationType.UPCOMING_MATCH: RENDER_NAMES[NotificationType.UPCOMING_MATCH],
    NotificationType.MATCH_SCORE: RENDER_NAMES[NotificationType.MATCH_SCORE],
    NotificationType.LEVEL_STARTING: RENDER_NAMES[NotificationType.LEVEL_STARTING],
    NotificationType.ALLIANCE_SELECTION: RENDER_NAMES[
        NotificationType.ALLIANCE_SELECTION
    ],
    NotificationType.AWARDS: RENDER_NAMES[NotificationType.AWARDS],
    NotificationType.SCHEDULE_UPDATED: RENDER_NAMES[NotificationType.SCHEDULE_UPDATED],
}


ENABLED_EVENT_NOTIFICATIONS: Set[NotificationType] = {
    NotificationType.UPCOMING_MATCH,
    NotificationType.MATCH_SCORE,
    NotificationType.LEVEL_STARTING,
    NotificationType.ALLIANCE_SELECTION,
    NotificationType.AWARDS,
    NotificationType.SCHEDULE_UPDATED,
    NotificationType.MATCH_VIDEO,
}


ENABLED_TEAM_NOTIFICATIONS: Set[NotificationType] = {
    NotificationType.UPCOMING_MATCH,
    NotificationType.MATCH_SCORE,
    NotificationType.ALLIANCE_SELECTION,
    NotificationType.AWARDS,
    NotificationType.MATCH_VIDEO,
}


ENABLED_MATCH_NOTIFICATIONS: Set[NotificationType] = {
    NotificationType.UPCOMING_MATCH,
    NotificationType.MATCH_SCORE,
    NotificationType.MATCH_VIDEO,
}
