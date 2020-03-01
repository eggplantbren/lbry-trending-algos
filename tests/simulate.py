import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rng

## Number of people using LBRY, and circulating supply (ballpark)
#num = 1000000
#supply = 5.0E8

## Lognormal LBC wealth distribution
#proportions = np.sort(np.exp(3.0*rng.randn(num)))
#proportions /= proportions.sum()
#net_worths = supply*proportions

## Whales are the top 0.1%
#whales = np.nonzero(net_worths >= net_worths[-num//1000])[0]

## Histogram of the whales' net worths
#plt.hist(np.log10(net_worths[whales]), 100)
#plt.xlabel("log10(net worth)")
#plt.show()

num = 100000

alpha = 1.0
ell = 134.0
k = 2.0**(-1.0/ell)
m = ell
L = np.exp(2-np.log(1.0 - rng.rand(num))/alpha)
y = L**0.25*k**(m*(1.0 - rng.rand(num)))

# Argsort by trending score
indices = np.argsort(y)
plt.hist(np.log10(L[indices][-1000:]), 100, density=True, alpha=0.2)

alpha = 1.0
ell = 134.0
k = 2.0**(-1.0/ell)
m = 1000.0
L = np.exp(2-np.log(1.0 - rng.rand(num))/alpha)
y = L**0.25*k**(m*(1.0 - rng.rand(num)))

indices = np.argsort(y)
plt.hist(np.log10(L[indices][-1000:]), 100, density=True, alpha=0.2)
plt.show()

