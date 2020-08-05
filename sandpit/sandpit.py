"""
A little demo of how trending calculations might be able to work.
"""
import apsw
import numpy as np

# A little database for the demo
conn = apsw.Connection("claims.db")
db = conn.cursor()

# Claims table
db.execute("""
CREATE TABLE IF NOT EXISTS claims
    (claim_hash BYTES NOT NULL PRIMARY KEY)
    WITHOUT ROWID;
""")

# Keep track of staked LBC changes (could be big)
db.execute("""
CREATE TABLE IF NOT EXISTS staked_amount_history
    (claim_hash BYTES NOT NULL,
     height     INTEGER NOT NULL,
     lbc        REAL NOT NULL,
     FOREIGN KEY (claim_hash) REFERENCES claims (claim_hash));
""")


# Some fake data for a claim that was created
# at block 801,000 and then had some LBC changes.
db.execute("""
DELETE FROM claims;
DELETE FROM staked_amount_history;
INSERT INTO claims VALUES ("hello") ON CONFLICT (claim_hash) DO NOTHING;
INSERT INTO staked_amount_history VALUES ("hello", 801000, 0.1),
                                         ("hello", 801000, 11.1),
                                         ("hello", 801200, 10011.1),
                                         ("hello", 801500, 0.1);
""")

# Trending parameter (a very basic version)
TIMESCALE = 200.0

def trending_score_at(current_height, claim_hash):
    """
    Compute the trending score at `height`.

    Could do it as an aggregate function
    or probably even some sort of signal processing operation (I think it might
    be related to convolution
    """

    # Extract relevant changes
    heights = []
    amounts = []
    for row in db.execute("SELECT height, lbc FROM staked_amount_history\
                           WHERE claim_hash=? AND height <= ?;",
                          ("hello", current_height)):
        heights.append(row[0])
        amounts.append(row[1])

    # Push starting value at the front
    amounts = [0.0] + amounts

    # Convert to numpy arrays
    heights = np.array(heights)
    amounts = np.array(amounts)

    # Diff to get changes
    changes = np.diff(amounts)

    # Soften
    changes = np.sign(changes)*np.abs(changes)**0.25

    return np.sum(changes*np.exp(-(current_height - heights)/TIMESCALE))


# Compute the trending score at a few block heights
for height in range(800000, 803001):
    print(height, trending_score_at(height, "hello"))


