import copy
import matplotlib.pyplot as plt
import math
import numpy as np
import numpy.random as rng
#import 

# Half life in blocks
HALF_LIFE = 134

# E-folding timescale
TIMESCALE = int(HALF_LIFE / np.log(2.0))

# Duration to simulate
DURATION = 5*TIMESCALE

# Decay coefficient per block
DECAY = 0.5**(1.0/HALF_LIFE)

def spike_height_experimental(trending_score, x, x_old, time_boost=1.0):
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


def generate_claim(func):
    """
    Simulate trajectory of a claim
    based on the given spike_height function
    """

    # Whether there was a big support in the past
    supported_at = DURATION - 1 + int(TIMESCALE*np.log(rng.rand()))
    support_amount = 10.0**(3.0 + 1.0*rng.randn())

    # Organic views
    views_start_at = DURATION - 1 + int(TIMESCALE*np.log(rng.rand()))
    autotip_prob = 10.0**(-3.0*rng.rand())

    # LBC value and trending score of the claim
    x = 0.0
    y = 0.0
    for i in range(DURATION):
        x_old = copy.deepcopy(x)
        if i == supported_at:
            x += support_amount
        if i >= views_start_at and rng.rand() <= autotip_prob:
            x += 1 + rng.randint(4)
        y = DECAY*y + func(y, x, x_old)

    return {"trending_score": y, "supported_at": supported_at,
            "support_amount": support_amount}


# Simulate 10000 claims and plot their trending scores
claims = []
for i in range(10000):
    claims.append(generate_claim(spike_height_experimental))
    print(len(claims))

trending_scores = np.array([claim["trending_score"] for claim in claims])
support_amounts = np.array([claim["support_amount"] for claim in claims])

plt.semilogx(support_amounts[trending_scores >= 200],
             trending_scores[trending_scores >= 200], ".", markersize=3, alpha=0.3)
plt.xlabel("Support size")
plt.ylabel("Trending score")
plt.show()

    
