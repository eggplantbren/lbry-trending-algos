import matplotlib.pyplot as plt
import math
import numpy as np
import numpy.random as rng

# Half life in blocks
HALF_LIFE = 134

# Decay coefficient per block
DECAY = 0.5**(1.0/HALF_LIFE)

def spike_height(trending_score, x, x_old, time_boost=1.0):
    """
    Compute the size of a trending spike.
    """

    # Magnitude of trending spike
    mag = abs(x - x_old)**0.95

    # Sign of trending spike
    sign = 1.0
    if x < x_old:
        sign = -1.0

    alpha = 0.8
    ell = 100.0
    x_ = max(x, x_old)
    mag *= ell**alpha*(x_ + ell)**(-alpha)

    return time_boost*sign*mag


def simulate_trajectory(total_lbc, blocks=1000):
    """
    Simulate a trajectory for trending scores
    """
    claim_lbc = 0.0
    trending_score = 0.0
    start = rng.randint(blocks)
    keep = np.empty(blocks)
    for i in range(blocks):
        old = 1.0*claim_lbc
        if i == start:
            claim_lbc += total_lbc
        trending_score = DECAY*trending_score + spike_height(trending_score, claim_lbc, old)
        keep[i] = trending_score

    plt.plot(keep)
    return keep


# Number of people using LBRY, and circulating supply (ballpark)
num = 1000000
supply = 5.0E8

# Lognormal LBC wealth distribution
proportions = np.sort(np.exp(3.0*rng.randn(num)))
proportions /= proportions.sum()
net_worths = supply*proportions
net_worths = np.sort(net_worths)[::-1]

for i in range(5):
    simulate_trajectory(net_worths[i])

plt.show()

    
