import math
from typing import Sequence, Final, Optional, Callable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from anki.cards import Card
from anki.stats_pb2 import CardStatsResponse

from .pbd import fast_poisson_binomial_pmf
from .utils import (
    group_card_reviews_by_day,
    SECONDS_PER_DAY,
    calculate_fsrs_4_5_retrievability,
    DayRevLog,
    filter_out_reviews_unwanted_by_fsrs,
)

_THRESHOLD_FACTOR: Final[float] = (math.pi**2) / 6
"""
Magic number used in calculating the corrected leech threshold
"""

type ThresholdFn = Callable[[float, int], float]


def _static_threshold(threshold: float, _n_trials: int) -> float:
    return threshold


def _calculate_corrected_threshold(alpha: float, n: int) -> float:
    """
    Calculate the corrected threshold for determining if a card is a leech.

    :param alpha: The base threshold probability.

    :param n: The number of trials / valid reviews.

    :return: The corrected threshold value based on the given parameters.
    """

    return alpha / (_THRESHOLD_FACTOR * (n**2))


@dataclass(frozen=True, slots=True)
class TrialsData:
    n_trials: int
    probabilities: npt.NDArray[np.float64]
    successes: npt.NDArray[np.bool]


def _calculate_trials_data(
    grouped_reviews: list[DayRevLog], skip_reviews: int, max_reviews: int
) -> Optional[TrialsData]:
    """
    Convert a list of reviews grouped by day into a list of Bernoulli trial
    probabilities and success/failure labels.

    :param grouped_reviews:
    :param skip_reviews:
    :return:
    """

    starting_idx = skip_reviews
    if max_reviews > 0:
        starting_idx = max(skip_reviews, len(grouped_reviews) - max_reviews)

    n_trials = len(grouped_reviews) - starting_idx
    if n_trials <= 0:
        return None

    trial_probabilities = np.zeros(n_trials, dtype=np.float64)
    trial_successes = np.zeros(n_trials, dtype=np.bool)
    for day_idx in range(starting_idx, len(grouped_reviews)):
        prev_review_day = grouped_reviews[day_idx - 1]
        curr_review_day = grouped_reviews[day_idx]

        canonical_prev_review = prev_review_day.reviews[-1]
        canonical_curr_review = curr_review_day.reviews[0]

        elapsed_days = (
            canonical_curr_review.time - canonical_prev_review.time
        ) / SECONDS_PER_DAY
        stability = canonical_prev_review.memory_state.stability

        r = calculate_fsrs_4_5_retrievability(elapsed_days, stability)

        trial_idx = day_idx - starting_idx
        trial_probabilities[trial_idx] = r
        trial_successes[trial_idx] = canonical_curr_review.button_chosen != 1

    return TrialsData(
        n_trials=n_trials,
        probabilities=trial_probabilities,
        successes=trial_successes,
    )


@dataclass(frozen=True, slots=True)
class IncrementalClassificationData:
    n_trials: int
    probabilities: npt.NDArray[np.float64]
    thresholds: npt.NDArray[np.float64]


def _calculate_incremental_leech_probabilities(
    trials_data: TrialsData,
    initial_threshold: float,
    threshold_fn: ThresholdFn,
) -> IncrementalClassificationData:
    """
    Calculate the probability of being a leech and the leech threshold after
    each trial.

    :param trials_data:
    :param initial_threshold:
    :param threshold_fn:
    :return:
    """

    leech_p = np.zeros(trials_data.n_trials, dtype=np.float64)
    leech_t = np.zeros(trials_data.n_trials, dtype=np.float64)
    for i in range(trials_data.n_trials):
        prob_subset = trials_data.probabilities[0 : i + 1]
        success_subset = trials_data.successes[0 : i + 1]

        success_count = success_subset.sum()

        pmf = fast_poisson_binomial_pmf(prob_subset)
        p = pmf[0 : success_count + 1].sum()

        actual_threshold = threshold_fn(initial_threshold, len(prob_subset))

        leech_p[i] = p
        leech_t[i] = actual_threshold

    return IncrementalClassificationData(
        n_trials=trials_data.n_trials,
        probabilities=leech_p,
        thresholds=leech_t,
    )


def _classify_with_total_history(
    trials_data: TrialsData,
    initial_threshold: float,
    threshold_fn: ThresholdFn,
) -> (bool, dict):
    pmf = fast_poisson_binomial_pmf(trials_data.probabilities)
    p = pmf[0 : trials_data.successes.sum() + 1].sum()

    actual_threshold = threshold_fn(initial_threshold, trials_data.n_trials)

    metadata = {
        "p": float(p),
        "t": actual_threshold,
    }

    return p < actual_threshold, metadata


def _classify_incrementally(
    trials_data: TrialsData,
    initial_threshold: float,
    threshold_fn: ThresholdFn,
) -> (bool, dict):
    leech_data = _calculate_incremental_leech_probabilities(
        trials_data=trials_data,
        initial_threshold=initial_threshold,
        threshold_fn=threshold_fn,
    )

    triggered_at_least_once = False
    last_triggered = False
    curr_triggered = False
    crossover_count = 0

    metadata = {}

    # Mark as leech as soon as we see it drop below the threshold
    for i in range(leech_data.n_trials):
        p = leech_data.probabilities[i]
        t = leech_data.thresholds[i]
        if p < t:
            triggered_at_least_once = True
            curr_triggered = True
        else:
            curr_triggered = False

        if curr_triggered != last_triggered:
            crossover_count += 1

        last_triggered = curr_triggered

    metadata["crossover_count"] = crossover_count

    return triggered_at_least_once, metadata


def card_is_leech(
    card: Card,
    reviews: Sequence[CardStatsResponse.StatsRevlogEntry],
    skip_reviews: int,
    max_reviews: int,
    leech_threshold: float,
    dynamic_threshold: bool,
    incremental_check: bool,
    next_day_starts_at_hour: int,
) -> (bool, Optional[float], Optional[float]):
    if skip_reviews < 1:
        raise Exception("skip_reviews must be at least 1")

    if leech_threshold < 0 or leech_threshold > 1:
        raise Exception("leech_threshold must be between 0 and 1")

    filtered_reviews = filter_out_reviews_unwanted_by_fsrs(reviews)
    grouped_reviews = group_card_reviews_by_day(
        filtered_reviews, next_day_starts_at_hour
    )

    trials_data = _calculate_trials_data(
        grouped_reviews=grouped_reviews,
        skip_reviews=skip_reviews,
        max_reviews=max_reviews,
    )

    # If we skipped everything just return leech=False
    if trials_data is None:
        return False, {}

    threshold_fn: ThresholdFn
    if dynamic_threshold:
        threshold_fn = _calculate_corrected_threshold
    else:
        threshold_fn = _static_threshold

    if incremental_check:
        return _classify_incrementally(
            trials_data=trials_data,
            initial_threshold=leech_threshold,
            threshold_fn=threshold_fn,
        )
    else:
        return _classify_with_total_history(
            trials_data=trials_data,
            initial_threshold=leech_threshold,
            threshold_fn=threshold_fn,
        )
