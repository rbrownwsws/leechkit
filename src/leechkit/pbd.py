import numpy as np


def fast_poisson_binomial_pmf(p: list):
    """
    Calculate the exact PMF of the Poisson Binomial distribution using
    dynamic programming and vectorized NumPy operations.

    Parameters:
    -----------
    p : array-like
        Array of success probabilities for each Bernoulli trial

    Returns:
    --------
    numpy array of PMF values for k=0,1,...,len(p)
    """
    p = np.asarray(p, dtype=np.float64)
    n = len(p)

    # Validate input
    if not np.all((0 <= p) & (p <= 1)):
        raise ValueError("All probabilities must be between 0 and 1")

    # Handle trivial cases
    if n == 0:
        return np.array([1.0])

    # Initialize the PMF - we'll use a dynamic programming approach
    # pmf[j] will represent P(X = j) after considering the first i trials
    pmf = np.zeros(n + 1, dtype=np.float64)
    pmf[0] = 1.0  # Base case: probability of 0 successes with 0 trials is 1

    # Process each probability one at a time
    for prob in p:
        # For each new Bernoulli trial, we update the entire PMF
        # We do this in reverse order to avoid overwriting values we still need
        # The key insight: P(X=k after adding new trial) =
        #   P(X=k with no success in new trial) + P(X=k-1 with success in new trial)

        # Calculate the effect of this probability on the entire PMF at once
        # This is where the vectorization happens
        pmf_shifted = np.zeros_like(pmf)
        pmf_shifted[1:] = pmf[:-1] * prob  # Probability of success for this trial

        # Update PMF by combining the two possibilities
        pmf = pmf * (1 - prob) + pmf_shifted  # No success + success for this trial

    return pmf
