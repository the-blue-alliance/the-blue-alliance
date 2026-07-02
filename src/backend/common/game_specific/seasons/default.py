from backend.common.game_specific.base import DefaultSeasonGameConfig


class DefaultGame(DefaultSeasonGameConfig):
    """Fallback used for years with no registered season-specific config."""

    pass
