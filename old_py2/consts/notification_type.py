class NotificationType(object):
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

    type_names = {
        UPCOMING_MATCH: "upcoming_match",
        MATCH_SCORE: "match_score",
        LEVEL_STARTING: "starting_comp_level",
        ALLIANCE_SELECTION: "alliance_selection",
        AWARDS: "awards_posted",
        MEDIA_POSTED: "media_posted",
        DISTRICT_POINTS_UPDATED: "district_points_updated",
        SCHEDULE_UPDATED: "schedule_updated",
        FINAL_RESULTS: "final_results",
        PING: "ping",
        BROADCAST: "broadcast",
        MATCH_VIDEO: "match_video",
        EVENT_MATCH_VIDEO: "event_match_video",

        UPDATE_FAVORITES: "update_favorites",
        UPDATE_SUBSCRIPTIONS: "update_subscriptions",

        VERIFICATION: "verification"
    }

    render_names = {
        UPCOMING_MATCH: "Upcoming Match",
        MATCH_SCORE: "Match Score",
        LEVEL_STARTING: "Competition Level Starting",
        ALLIANCE_SELECTION: "Alliance Selection",
        AWARDS: "Awards Posted",
        MEDIA_POSTED: "Media Posted",
        DISTRICT_POINTS_UPDATED: "District Points Updated",
        SCHEDULE_UPDATED: "Event Schedule Updated",
        FINAL_RESULTS: "Final Results",
        MATCH_VIDEO: "Match Video Added",
        EVENT_MATCH_VIDEO: "Match Video Added",
    }

    types = {
        "upcoming_match": UPCOMING_MATCH,
        "match_score": MATCH_SCORE,
        "starting_comp_level": LEVEL_STARTING,
        "alliance_selection": ALLIANCE_SELECTION,
        "awards_posted": AWARDS,
        "media_posted": MEDIA_POSTED,
        "district_points_updated": DISTRICT_POINTS_UPDATED,
        "schedule_updated": SCHEDULE_UPDATED,
        "final_results": FINAL_RESULTS,
        "match_video": MATCH_VIDEO,
        "event_match_video": EVENT_MATCH_VIDEO,

        "update_favorites": UPDATE_FAVORITES,
        "update_subscriptions": UPDATE_SUBSCRIPTIONS,

        "verification": VERIFICATION
    }

    enabled_notifications = {
        UPCOMING_MATCH: render_names[UPCOMING_MATCH],
        MATCH_SCORE: render_names[MATCH_SCORE],
        LEVEL_STARTING: render_names[LEVEL_STARTING],
        ALLIANCE_SELECTION: render_names[ALLIANCE_SELECTION],
        AWARDS: render_names[AWARDS],
        SCHEDULE_UPDATED: render_names[SCHEDULE_UPDATED],
    }

    enabled_event_notifications = [
        UPCOMING_MATCH,
        MATCH_SCORE,
        LEVEL_STARTING,
        ALLIANCE_SELECTION,
        AWARDS,
        SCHEDULE_UPDATED,
        MATCH_VIDEO,
    ]

    enabled_team_notifications = [
        UPCOMING_MATCH,
        MATCH_SCORE,
        ALLIANCE_SELECTION,
        AWARDS,
        MATCH_VIDEO,
    ]

    enabled_match_notifications = [
        UPCOMING_MATCH,
        MATCH_SCORE,
        MATCH_VIDEO,
    ]
