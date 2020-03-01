import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rng

# Number of people using LBRY, and circulating supply (ballpark)
num = 1000000
supply = 5.0E8

# Lognormal LBC wealth distribution
proportions = np.sort(np.exp(3.0*rng.randn(num)))
proportions /= proportions.sum()
net_worths = supply*proportions

# Trending half life
ell = 134.0
k = 2.0**(-1.0/ell)

# Boosting intervals
m = 134

# Softening power
soften = 0.25

# Trending scores
ys = net_worths**soften*k**(m*(1.0 - rng.rand(num)))

# Sort trending scores
indices = np.argsort(ys)
ranks = np.empty(num)
ranks[indices] = np.arange(num)
high = ranks >= num - 100

# Plot LBC vs trending rank
plt.semilogy(ranks[high], net_worths[high], "o", markersize=5, alpha=0.2)
plt.show()

