import os
import sys
from datetime import timezone, date, datetime, tzinfo
from typing import Final, Optional, Sequence

from anki.stats_pb2 import CardStatsResponse

SECONDS_PER_DAY: Final[int] = 86_400
SECONDS_PER_HOUR: Final[int] = 3_600

_FSRS_DECAY: Final[float] = -0.5
_FSRS_FACTOR: Final[float] = 19 / 81


class SuppressPrint:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def calculate_fsrs_4_5_retrievability(elapsed_days: float, stability: float) -> float:
    """
    Calculates the retrievability of a card based on the FSRS-4.5 equation.

    :param elapsed_days: The number of days since the last review.

    :param stability: The estimated interval (in days) in which retrievability
                      will drop from `1.0` to `0.9`.

    :return: The probability of correctly recalling a card.
    """

    return (1 + (_FSRS_FACTOR * elapsed_days / stability)) ** _FSRS_DECAY


class DayRevLog:
    """
    Represents a list of reviews for a single card that occurred on the same
    effective day.

    :ivar effective_date: The date on which the reviews took place
                          (taking into account "Next day starts at").
    :ivar reviews: A list of review entries for the card on this effective date.
    """

    effective_date: date
    reviews: list[CardStatsResponse.StatsRevlogEntry]

    def __init__(self, effective_date: date):
        self.effective_date = effective_date
        self.reviews = []


def calculate_review_effective_date(
    timestamp_s: int, next_day_starts_at_hour: int, tz: tzinfo = timezone.utc
) -> date:
    """
    Calculate the effective date that a review occurred on taking account of the "Next day starts at" setting.

    :param timestamp_s:
    :param next_day_starts_at_hour:
    :param tz:
    :return:
    """

    day_start_offset_s = next_day_starts_at_hour * SECONDS_PER_HOUR
    offset_timestamp_s = timestamp_s - day_start_offset_s

    # TODO: Figure out how the timezone works.
    #       Does Anki store the timezone anywhere or do we just have use the current system timezone?

    return datetime.fromtimestamp(
        timestamp=offset_timestamp_s,
        tz=tz,
    ).date()


def group_card_reviews_by_day(
    reviews: Sequence[CardStatsResponse.StatsRevlogEntry], next_day_starts_at_hour: int
) -> list[DayRevLog]:
    """
    Group a cards reviews by the effective day they occurred.

    :param reviews: A list of reviews for a card. These reviews **must** be sorted from oldest to newest.

    :param next_day_starts_at_hour:

    :return:
    """

    grouped_reviews = []
    current_day_reviews: Optional[DayRevLog] = None

    for review in reviews:
        review_effective_date = calculate_review_effective_date(
            review.time, next_day_starts_at_hour
        )

        if (
            current_day_reviews is None
            or current_day_reviews.effective_date != review_effective_date
        ):
            current_day_reviews = DayRevLog(review_effective_date)
            grouped_reviews.append(current_day_reviews)

        current_day_reviews.reviews.append(review)

    return grouped_reviews
