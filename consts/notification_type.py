class NotificationType(object):
    """
    Constants regarding the different types of notification we can send to a device
    See https://docs.google.com/document/d/1SV-hNCtgAn2hSMZaC973UdLHCFXCNpvq_RKq0UoY4yg/edit#
    """

    # DO NOT CHANGE THESE CONSTANTS
    UPCOMING_MATCH = "upcoming_match"
    MATCH_SCORE = "match_score"
    LEVEL_STARTING = "starting_comp_level"
    ALLIANCE_SELECTION = "alliance_selection"
    AWARDS = "awards_posted"
    MEDIA_POSTED = "media_posted"
    DISTRICT_POINTS_UPDATED = "district_points_updated"
    SCHEDULE_POSTED = "schedule_posted"
    FINAL_RESULTS = "final_results"

    UPDATE_FAVORITES = "update_favorites"
    UPDATE_SUBSCIPTION = "update_subscriptions"
