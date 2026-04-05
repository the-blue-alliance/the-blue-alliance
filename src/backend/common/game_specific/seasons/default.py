from backend.common.game_specific.base import SeasonGameConfig


class DefaultGame(SeasonGameConfig):
    """Fallback used for years with no registered season-specific config."""

    pass
