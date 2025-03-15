import math
from typing import Sequence, Final, Optional


from anki.cards import Card
from anki.stats_pb2 import CardStatsResponse

from .pbd import fast_poisson_binomial_pmf
from .utils import (
    group_card_reviews_by_day,
    SECONDS_PER_DAY,
    calculate_fsrs_4_5_retrievability,
)

_THRESHOLD_FACTOR: Final[float] = (math.pi**2) / 6
"""
Magic number used in calculating the corrected leech threshold
"""


def _calculate_corrected_threshold(alpha: float, n: int) -> float:
    """
    Calculate the corrected threshold for determining if a card is a leech.

    :param alpha: The base threshold probability.

    :param n: The number of trials / valid reviews.

    :return: The corrected threshold value based on the given parameters.
    """

    return alpha / (_THRESHOLD_FACTOR * (n**2))


def card_is_leech(
    card: Card,
    reviews: Sequence[CardStatsResponse.StatsRevlogEntry],
    skip_reviews: int,
    leech_threshold: float,
    dynamic_threshold: bool,
    next_day_starts_at_hour: int,
) -> (bool, Optional[float], Optional[float]):
    if skip_reviews < 1:
        raise Exception("skip_reviews must be at least 1")

    if leech_threshold < 0 or leech_threshold > 1:
        raise Exception("leech_threshold must be between 0 and 1")

    grouped_reviews = group_card_reviews_by_day(reviews, next_day_starts_at_hour)

    # If we are going to skip everything just return leech=False
    if len(grouped_reviews) <= skip_reviews:
        return False, None, None

    trial_probabilities = []
    trial_success_count = 0

    for idx in range(skip_reviews, len(grouped_reviews)):
        prev_review_day = grouped_reviews[idx - 1]
        curr_review_day = grouped_reviews[idx]

        canonical_prev_review = prev_review_day.reviews[-1]
        canonical_curr_review = curr_review_day.reviews[0]

        elapsed_days = (
            canonical_curr_review.time - canonical_prev_review.time
        ) / SECONDS_PER_DAY
        stability = canonical_prev_review.memory_state.stability

        r = calculate_fsrs_4_5_retrievability(elapsed_days, stability)

        trial_probabilities.append(r)

        if canonical_curr_review.button_chosen != 1:
            trial_success_count += 1

    pmf = fast_poisson_binomial_pmf(trial_probabilities)
    p = sum(pmf[0 : trial_success_count + 1])

    if dynamic_threshold:
        actual_threshold = _calculate_corrected_threshold(
            leech_threshold, len(trial_probabilities)
        )
    else:
        actual_threshold = leech_threshold

    return p < actual_threshold, p, actual_threshold
