from typing import NamedTuple


class InsightV2NameEntry(NamedTuple):
    name: str
    display_name: str


class InsightV2Names:
    # Leaderboards
    BLUE_BANNERS = InsightV2NameEntry("blue_banners", "Total Blue Banners")
    MOST_MATCHES_PLAYED = InsightV2NameEntry(
        "most_matches_played", "Most Matches Played"
    )
    MOST_MATCHES_PLAYED_TOGETHER = InsightV2NameEntry(
        "most_matches_played_together", "Most Matches Played Together"
    )
    MOST_DIVISION_FINALS_APPEARANCES = InsightV2NameEntry(
        "most_division_finals_appearances", "Most Division Finals Appearances"
    )
    MOST_DIVISION_WINS = InsightV2NameEntry("most_division_wins", "Most Division Wins")
    MOST_CMP_FINALS_APPEARANCES = InsightV2NameEntry(
        "most_cmp_finals_appearances", "Most World Championship Finals Appearances"
    )
    MOST_CMP_WINS = InsightV2NameEntry("most_cmp_wins", "Most World Championship Wins")
    MOST_EVENTS_WON = InsightV2NameEntry("most_events_won", "Most Events Won")
    MOST_EVENTS_WON_TOGETHER = InsightV2NameEntry(
        "most_events_won_together", "Most Events Won Together"
    )
    MOST_IMPACT_AWARD_WINS = InsightV2NameEntry(
        "most_impact_award_wins", "Most Impact Award Wins"
    )
    MOST_AWARDS_WON = InsightV2NameEntry("most_awards_won", "Most Awards Won")
    MOST_DISTRICT_CMP_WINS = InsightV2NameEntry(
        "most_district_cmp_wins", "Most District Championship Wins"
    )
    MOST_WFFA_WINS = InsightV2NameEntry("most_wffa_wins", "Most WFFAs")
    HIGHEST_MATCH_CLEAN_SCORE = InsightV2NameEntry(
        "highest_match_clean_score", "Highest Clean Score"
    )
    HIGHEST_MATCH_CLEAN_COMBINED_SCORE = InsightV2NameEntry(
        "highest_match_clean_combined_score", "Highest Combined Clean Score"
    )

    # Streaks
    QUALIFYING_EVENT_WIN_STREAK = InsightV2NameEntry(
        "qualifying_event_win_streak", "Longest Qualifying Event Win Streak"
    )
    EINSTEIN_WIN_STREAK = InsightV2NameEntry(
        "einstein_streak", "Longest Einstein Streak"
    )
    UNDEFEATED_STREAK = InsightV2NameEntry(
        "undefeated_streak", "Longest Undefeated Season Start"
    )
    WIN_STREAK = InsightV2NameEntry("win_streak", "Longest Win Streak")

    # Timeseries
    HIGH_SCORE_OVER_TIME = InsightV2NameEntry(
        "high_score_over_time", "High Score Over Time"
    )
