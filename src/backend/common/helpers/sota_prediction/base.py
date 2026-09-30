"""Base predictor interface for FRC match prediction benchmarking.

Defines the abstract base class BasePredictor that all prediction algorithms
must inherit from and implement. Enforces the strict two-phase protocol separating
pre-match prediction (`predict_match`) from post-match state updates (`update`).
"""

from __future__ import annotations

import abc
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import MatchContext
    from .outcome import MatchOutcome
    from .predictions import MatchPrediction


class BasePredictor(abc.ABC):
    """Abstract base class for all FRC match prediction algorithms.

    Subclasses must implement:
    1. `predict_match(self, context: MatchContext) -> MatchPrediction`:
       Called during Phase 1 of replay. Evaluates the match using strictly
       pre-match information in the immutable MatchContext container. Any
       attempt to access post-match scores or outcomes triggers TemporalViolationError.
    2. `update(self, outcome: MatchOutcome) -> None`:
       Called during Phase 2 of replay. Finalized match results (scores, winner,
       ranking points, breakdowns) are delivered to update internal ratings or
       model state only after predictions have been recorded.

    Optional lifecycle hooks:
    - `reset()`: Resets all internal learned state.
    - `start_season(season)`: Invoked before a season's match replay begins.
    - `end_season(season)`: Invoked after a season's match replay completes.
    """

    # Model independence metadata:
    # Set is_standalone = False and populate external_dependencies if the model wraps,
    # queries, or ensembles any external model (e.g., Match13).
    is_standalone: bool = True
    external_dependencies: tuple[str, ...] = ()

    # First season the model can replay. None means every season. The runner
    # drops warmup matches from earlier seasons for this model and refuses to
    # score any season before it, so all models score the same population.
    first_supported_season: Optional[int] = None

    def __init__(self, name: Optional[str] = None) -> None:
        """Initialize predictor with optional model name.

        Args:
            name: Human-readable model identifier. Defaults to class name.
        """
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        """Return the model identifier name."""
        return self._name

    @abc.abstractmethod
    def predict_match(self, context: MatchContext) -> MatchPrediction:
        """Compute pre-match prediction using only pre-match context.

        Args:
            context: Immutable pre-match container. Access to scores, winner,
                breakdown, or earned RPs raises TemporalViolationError.

        Returns:
            MatchPrediction instance containing win probability, score forecasts,
            and optional ranking point forecasts.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, outcome: MatchOutcome) -> None:
        """Update predictor state or ratings with finalized match outcome.

        This method is invoked only after `predict_match()` has completed and
        the benchmark harness has committed the prediction to the evaluation log.

        Args:
            outcome: Finalized post-match result container including scores,
                winning alliance, score breakdown, and earned ranking points.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Reset internal model state, learned weights, and rating parameters.

        Default implementation is a no-op for stateless models. Stateful models
        (e.g., Elo, Bayesian ratings, running averages) must override this to
        ensure clean isolation between benchmark runs.
        """
        pass

    def start_season(self, season: int) -> None:
        """Hook called before replaying a season's match stream.

        Optional lifecycle hook for models supporting season-to-season transitions
        (e.g., Elo regression to the mean between years). Default is a no-op.

        Args:
            season: The 4-digit FRC season year being started.
        """
        pass

    def end_season(self, season: int) -> None:
        """Hook called after completing a season's match stream.

        Optional lifecycle hook for post-season cleanup or diagnostics. Default is a no-op.

        Args:
            season: The 4-digit FRC season year just completed.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
