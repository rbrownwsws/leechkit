from datetime import date
from typing import Final

from leechkit.utils import calculate_review_effective_date

CHRISTMAS_2024_2AM_TIMESTAMP: Final[int] = 1735092000


def test_no_offset():
    assert calculate_review_effective_date(CHRISTMAS_2024_2AM_TIMESTAMP, 0) == date(
        year=2024, month=12, day=25
    )


def test_offset():
    assert calculate_review_effective_date(CHRISTMAS_2024_2AM_TIMESTAMP, 3) == date(
        year=2024, month=12, day=24
    )
