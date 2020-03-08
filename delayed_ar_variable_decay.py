"""
Delayed AR with variable decay rate.

The spike height function is also simpler.
"""

import copy
import math
import random
import time

# Half life in blocks *for lower LBC claims* (it's shorter for whale claims)
HALF_LIFE = 134

# Whale threshold (higher -> less DB writing)
WHALE_THRESHOLD = 10000.0
WHALE_TRENDING_THRESHOLD = 50.0

# Decay coefficient per block
DECAY = 0.5**(1.0/HALF_LIFE)

# How frequently to write trending values to the db
SAVE_INTERVAL = 10

# Renormalisation interval
RENORM_INTERVAL = 1000

# Assertion
assert RENORM_INTERVAL % SAVE_INTERVAL == 0

# Decay coefficient per renormalisation interval
DECAY_PER_RENORM = DECAY**(RENORM_INTERVAL)

# Log trending calculations?
TRENDING_LOG = True


def install(connection):
    """
    Install the AR trending algorithm.
    """
    check_trending_values(connection)

    if TRENDING_LOG:
        f = open("trending_ar.log", "a")
        f.close()

# Stub
CREATE_TREND_TABLE = ""


def check_trending_values(connection):
    """
    If the trending values appear to be based on the zscore algorithm,
    reset them. This will allow resyncing from a standard snapshot.
    """
    c = connection.cursor()
    needs_reset = False
    for row in c.execute("SELECT COUNT(*) num FROM claim WHERE trending_global <> 0;"):
        if row[0] != 0:
            needs_reset = True
            break

    if needs_reset:
        print("Resetting some columns. This might take a while...", flush=True, end="")
        c.execute(""" BEGIN;
                      UPDATE claim SET trending_group = 0;
                      UPDATE claim SET trending_mixed = 0;
                      UPDATE claim SET trending_global = 0;
                      UPDATE claim SET trending_local = 0;
                      COMMIT;""")
        print("done.")


def spike_height(trending_score, x, x_old):
    """
    Compute the size of a trending spike (normed - constant units).
    """

    # Sign of trending spike
    sign = 1.0
    if x < x_old:
        sign = -1.0

    # Magnitude
    alpha = 1.0
    ell = 100.0
    x_ = max(x, x_old)
    mag = abs(x - x_old) * ell**alpha*(x_ + ell)**(-alpha)

    return sign*mag



def get_time_boost(height):
    """
    Return the time boost at a given height.
    """
    return 1.0/DECAY**(height % RENORM_INTERVAL)


def trending_log(s):
    """
    Log a string.
    """
    if TRENDING_LOG:
        fout = open("trending_ar.log", "a")
        fout.write(s)
        fout.flush()
        fout.close()

class TrendingData:
    """
    An object of this class holds trending data
    """
    def __init__(self):

        # Dict from claim id to some trending info.
        # Units are TIME VARIABLE in here
        self.claims = {}

        # Claims with >= WHALE_THRESHOLD LBC total amount
        self.whales = set([])

        # Have all claims been read from db yet?
        self.initialised = False

        # List of pending spikes.
        # Units are CONSTANT in here
        self.pending_spikes = []

    def insert_claim_from_load(self, claim_hash, trending_score, total_amount):
        assert not self.initialised
        self.claims[claim_hash] = {"trending_score": trending_score,
                                   "total_amount": total_amount,
                                   "changed": False}
        self.update_whale_list(claim_hash)


    def update_whale_list(claim_hash, trending_normed=None):

        if trending_normed is None:
            trending_normed = self.claims[claim_hash]["trending_score"]/get_time_boost(height)

        # Check for "ex-whale" status
        if claim_hash in self.whales and \
                (total_amount < WHALE_THRESHOLD and trending_normed < WHALE_TRENDING_THRESHOLD):
            self.whales.remove(claim_hash)

        # Check for new/existing whale status
        if total_amount >= WHALE_THRESHOLD or trending_normed >= WHALE_TRENDING_THRESHOLD:
            self.whales.add(claim_hash)


    def apply_spikes(self, height):
        """
        Apply all pending spikes that are due at this height.
        Apply with time boost ON.
        """
        time_boost = get_time_boost(height)

        for spike in self.pending_spikes:
            if spike["height"] > height:
                # Ignore
                pass
            if spike["height"] == height:
                # Apply
                self.claims[spike["claim_hash"]]["trending_score"] += time_boost*spike["size"]
                self.claims[spike["claim_hash"]]["changed"] = True

        # Keep only future spikes
        self.pending_spikes = [s for s in self.pending_spikes \
                               if s["height"] > height]


    def update_claim(self, height, claim_hash, total_amount):
        """
        Update trending data for a claim, given its new total amount.
        """
        assert self.initialised

        # Extract existing total amount and trending score
        # or use starting values if the claim is new
        if claim_hash in self.claims:
            old_state = copy.deepcopy(self.claims[claim_hash])
        else:
            old_state = {"trending_score": 0.0,
                         "total_amount": 0.0,
                         "changed": False}

        # Convert to constant units
        trending_normed = old_state["trending_score"]/get_time_boost(height)
        self.update_whale_list(claim_hash, trending_normed)

        # Calculate LBC change
        change = total_amount - old_state["total_amount"]

        # Modify data if there was an LBC change
        if change != 0.0:
            spike = spike_height(trending_normed,
                                 total_amount,
                                 old_state["total_amount"])
            delay = min(int((total_amount + 1E-8)**(1/3)), 3*HALF_LIFE)

            if change < 0.0:

                # How big would the spike be for the inverse movement?
                reverse_spike = spike_height(old_state["trending_score"]/get_time_boost(height),
                                             old_state["total_amount"], total_amount)

                # Remove that much spike from future pending ones
                for future_spike in self.pending_spikes:
                    if future_spike["claim_hash"] == claim_hash:
                        if reverse_spike >= future_spike["size"]:
                            reverse_spike -= future_spike["size"]
                            future_spike["size"] = 0.0
                        elif reverse_spike > 0.0:
                            future_spike["size"] -= reverse_spike
                            reverse_spike = 0.0

                delay = 0
                spike -= reverse_spike

            self.pending_spikes.append({"height": height + delay,
                                        "claim_hash": claim_hash,
                                        "size": spike})

            self.claims[claim_hash] = {"total_amount": total_amount,
                                       "trending_score": old_state["trending_score"],
                                       "changed": False}

        # Make bigger claims decay faster
        if height % SAVE_INTERVAL == 0:

            # Total LBC
            if claim_hash in self.whales and total_amount >= WHALE_THRESHOLD:
                self.claims[claim_hash]["trending_score"] *= \
                            (DECAY**SAVE_INTERVAL)**(5*math.log10(total_amount/WHALE_THRESHOLD))
                self.claims[claim_hash]["changed"] = True

            # Trending score
            if claim_hash in self.whales and trending_normed >= WHALE_TRENDING_THRESHOLD:
                self.claims[claim_hash]["trending_score"] *= \
                            (DECAY**SAVE_INTERVAL)**(5*math.log10(trending_normed/WHALE_TRENDING_THRESHOLD))
                self.claims[claim_hash]["changed"] = True


def test_trending():
    """
    Quick trending test for claims with different support patterns
    """
    data = TrendingData()
    data.initialised = True

    height = 0
    data.update_claim(height, "whale_claim_one_support", 0.01)
    data.update_claim(height, "whale_claim_botted", 0.01)
    data.update_claim(height, "popular_minnow_claim", 0.01)
    data.update_claim(height, "dolphin_claim", 0.01)
    data.update_claim(height, "whale_claim_one_support",
                      data.claims["whale_claim_one_support"]["total_amount"] + 5E5)
    data.update_claim(height, "dolphin_claim",
                      data.claims["dolphin_claim"]["total_amount"] + 1E3)
#    data.update_claim(height, "random_claim", 10.0**random.gauss(2.0, 2.0))
    data.apply_spikes(height)

    # Save trajectories
    trajectories = {}
    for key in data.claims:
        trajectories[key] = [data.claims[key]["trending_score"]]

    for height in range(1, 5000):

        if height % RENORM_INTERVAL == 0:
            for key in data.claims:
                data.claims[key]["trending_score"] *= DECAY_PER_RENORM

#        # The random claim
#        if random.uniform(0.0, 1.0) <= 0.003:
#            data.update_claim(height, "random_claim", 10.0**random.gauss(2.0, 2.0))

        # Add new supports
        if height <= 500:
            data.update_claim(height, "whale_claim_botted",
                              data.claims["whale_claim_botted"]["total_amount"] + 5E5/500)
            data.update_claim(height, "popular_minnow_claim",
                              data.claims["popular_minnow_claim"]["total_amount"] + 1.0)

        # Abandon all supports
        if height == 500:
            for key in data.claims:
                data.update_claim(height, key, 0.01)

        data.apply_spikes(height)

        for key in data.claims:
            trajectories[key].append(data.claims[key]["trending_score"]/get_time_boost(height))

    import matplotlib.pyplot as plt
    for key in data.claims:
        plt.plot(trajectories[key], label=key)
    plt.legend()
    plt.show()


# One global instance
# pylint: disable=C0103
trending_data = TrendingData()

def run(db, height, final_height, recalculate_claim_hashes):

    if height < final_height - 5*HALF_LIFE:
        trending_log("Skipping AR trending at block {h}.\n".format(h=height))
        return

    start = time.time()

    trending_log("Calculating AR trending at block {h}.\n".format(h=height))
    trending_log("    Length of trending data = {l}.\n"\
                        .format(l=len(trending_data.claims)))

    # Renormalise trending scores and mark all as having changed
    if height % RENORM_INTERVAL == 0:
        trending_log("    Renormalising trending scores...")

        keys = trending_data.claims.keys()
        for key in keys:
            if trending_data.claims[key]["trending_score"] != 0.0:
                trending_data.claims[key]["trending_score"] *= DECAY_PER_RENORM
                trending_data.claims[key]["changed"] = True

                # Tiny becomes zero
                if abs(trending_data.claims[key]["trending_score"]) < 1E-3:
                    trending_data.claims[key]["trending_score"] = 0.0

        trending_log("done.\n")


    # Regular message.
    trending_log("    Reading total_amounts from db and updating"\
                        + " trending scores in RAM...")

    # Update claims from db
    if not trending_data.initialised:
        # On fresh launch
        for row in db.execute("""
                              SELECT claim_hash, trending_mixed,
                                     (amount + support_amount)
                                         AS total_amount
                              FROM claim;
                              """):
            trending_data.insert_claim_from_load(row[0], row[1], 1E-8*row[2])
        trending_data.initialised = True
    else:
        for row in db.execute(f"""
                              SELECT claim_hash,
                                     (amount + support_amount)
                                         AS total_amount
                              FROM claim
                              WHERE claim_hash IN
                            ({','.join('?' for _ in recalculate_claim_hashes)});
                              """, recalculate_claim_hashes):
            trending_data.update_claim(height, row[0], 1E-8*row[1])

        # Apply pending spikes
        trending_data.apply_spikes(height)

    trending_log("done.\n")


    # Write trending scores to DB
    if height % SAVE_INTERVAL == 0:

        trending_log("    Writing trending scores to db...")

        the_list = []
        keys = trending_data.claims.keys()

        for key in keys:
            if trending_data.claims[key]["changed"]:
                the_list.append((trending_data.claims[key]["trending_score"], key))
                trending_data.claims[key]["changed"] = False

        trending_log("{n} scores to write...".format(n=len(the_list)))

        db.executemany("UPDATE claim SET trending_mixed=? WHERE claim_hash=?;",
                       the_list)

        trending_log("done.\n")

    trending_log("Trending operations took {time} seconds.\n\n"\
                            .format(time=time.time() - start))


if __name__ == "__main__":
    test_trending()
