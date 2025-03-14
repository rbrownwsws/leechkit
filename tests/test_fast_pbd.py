import numpy as np
import pytest
from hypothesis import given, example, strategies as st
from scipy.stats import poisson_binom

from leechkit.pbd import fast_poisson_binomial_pmf


@given(st.lists(min_size=1, elements=st.floats(min_value=0.0, max_value=1.0)))
@example([0.5, 0.5, 0.5, 0.5])
def test_fast_pbd_pmf(probabilities: list[float]) -> None:
    fast_result = fast_poisson_binomial_pmf(probabilities)

    scipy_result = np.zeros(len(probabilities) + 1)
    for k in range(len(probabilities) + 1):
        scipy_result[k] = poisson_binom.pmf(k, probabilities)

    assert fast_result == pytest.approx(scipy_result)
