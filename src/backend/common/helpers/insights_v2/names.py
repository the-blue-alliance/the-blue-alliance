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

    # Streaks
    QUALIFYING_EVENT_WIN_STREAK = InsightV2NameEntry(
        "qualifying_event_win_streak", "Longest Qualifying Event Win Streak"
    )
    EINSTEIN_WIN_STREAK = InsightV2NameEntry(
        "einstein_streak", "Longest Einstein Streak"
    )
