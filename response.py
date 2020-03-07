import matplotlib.pyplot as plt
import math
import numpy as np

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



def update_lbc(i, lbc, strategy, revoke_at_block=False):

    if revoke_at_block is not None and i == revoke_at_block:
        lbc[i] = 0.0
        return

    if i == 0 or (i-1) % strategy["gap"] != 0 \
                    or i >= 1 + strategy["gap"]*strategy["num_supports"]:
        lbc[i] = lbc[i-1]
    else:
        lbc[i] = lbc[i-1] + strategy["total_lbc"]/strategy["num_supports"]


def simulate_strategy(t, strategy, revoke_at_block=False):
    lbc = np.empty(len(t))
    trending = np.empty(len(t))

    lbc[0] = 0.0
    trending[0] = 0.0

    for i in range(1, len(t)):
        update_lbc(i, lbc, strategy, revoke_at_block)
        trending[i] = DECAY*trending[i-1] + spike_height(trending[i-1], lbc[i], lbc[i-1])

    return {"lbc": lbc, "trending": trending}


if __name__ == "__main__":

    # Timespan of the simulation in blocks
    t = np.arange(0, 1001)

    plt.figure(figsize=(11, 7))

    strategy = {"num_supports": 1, "gap": 1, "total_lbc": 100000}
    trending = simulate_strategy(t, strategy)["trending"]
    plt.plot(t/24.0, trending, label="100K LBC in a single support")

    strategy = {"num_supports": 1, "gap": 1, "total_lbc": 10000}
    trending = simulate_strategy(t, strategy, revoke_at_block=576)["trending"]
    plt.plot(t/24.0, trending, label="10K LBC in a single support, revoked after 24h")

    strategy = {"num_supports": 5, "gap": 220, "total_lbc": 10000}
    trending = simulate_strategy(t, strategy)["trending"]
    plt.plot(t/24.0, trending, label="10K divided over five supports")

    strategy = {"num_supports": 576, "gap": 1, "total_lbc": 5*576}
    trending = simulate_strategy(t, strategy)["trending"]
    plt.plot(t/24.0, trending, label=\
            "5 LBC every block for 24 hours (total LBC={tot})"\
            .format(tot=strategy["total_lbc"]))

    plt.xlabel("Time (hours)")
    plt.ylabel("Trending score")
    plt.legend()
    plt.savefig("response.svg")
    plt.show()
