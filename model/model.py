"""v1 crew-hiring patterns (k-means) on the NYU Student Film Crewing Survey.

Business question: how can we identify distinct crew-hiring patterns to improve
recruitment recommendations for student filmmakers?

Use: when someone posts a job, their past hires place them in a hiring pattern,
and the pattern sets their discover page (personalized recommendations).

Standalone: loads the survey, fits v1, prints the fit evaluation (elbow on the
training hires; baseline vs v1 spread on the test hires), and returns the
discover page for a new job post.

    python model.py          # new post by producer 6, using their past hires
    python model.py 9        # same for producer 9

Model fit uses only survey fields. Dollar figures in the value section are FICTIONAL ASSUMPTIONS.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "src"))
from prep import METHODS, load  # noqa: E402

OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)
SEED = 42
K_RANGE = range(1, 7)
K_CHOSEN = 3
OUTCOMES = ["performance", "rehire_yes", "flaked_yes"]

# ------------------------------------------------------------------ data + split
hires = load(HERE / "data" / "survey_anonymized.xlsx")
hires.to_csv(OUT / "hires_clean.csv", index=False)

# Features: how easy the hire was to find, plus each search method used in at least
# 10 of the hires. Methods used 1-3 times are left out (too rare to define a group).
# Performance, rehire and flaked are left out of the fit; they describe the segments.
COMMON = [m for m in METHODS if hires[m].sum() >= 10]
FEATURES = ["ease"] + COMMON

train, test = train_test_split(hires, test_size=0.30, random_state=SEED)
scaler = StandardScaler().fit(train[FEATURES])
X_train, X_test = scaler.transform(train[FEATURES]), scaler.transform(test[FEATURES])

# ------------------------------------------------------------------ fit k = 1..6
models, train_sse, test_sse = {}, {}, {}
for k in K_RANGE:
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(X_train)
    models[k] = km
    train_sse[k] = km.inertia_
    d2 = ((X_test[:, None, :] - km.cluster_centers_[None, :, :]) ** 2).sum(axis=2)
    test_sse[k] = d2.min(axis=1).sum()  # trained centres, no refit
model = models[K_CHOSEN]

# Label segments 1..k by centroid ease, easiest first (names are for the team to choose).
centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=FEATURES)
order = centers["ease"].sort_values(ascending=False).index
label = {c: f"Segment {i + 1}" for i, c in enumerate(order)}
centers["segment"] = centers.index.map(label)

hires["segment"] = [label[c] for c in model.predict(scaler.transform(hires[FEATURES]))]
hires["set"] = np.where(hires.index.isin(train.index), "train", "test")

# ------------------------------------------------------------------ baseline vs v1, in survey units
baseline = hires[OUTCOMES].mean().round(3).to_dict() | {"hires": len(hires)}
profile = hires.groupby("segment").agg(
    hires=("role", "size"), **{f: (f, "mean") for f in FEATURES + OUTCOMES}
).round(2)


# ------------------------------------------------------------------ value: FICTIONAL ASSUMPTIONS
# None of these figures come from the survey. They are made up for illustration
# and must be labelled as assumptions on the slides.
ASSUMED_VET_COST = 15.0        # ASSUMPTION: $ cost to vet one hire (reference check / verification)
ASSUMED_FLAKE_COST = 300.0     # ASSUMPTION: $ a last-minute flake costs a production (replacement, lost time)
ASSUMED_FLAKES_PREVENTED = 0.5 # ASSUMPTION: share of flakes vetting prevents


def vet_net(flaked):
    """Net $ from vetting one hire, applied hire by hire using the survey's flake answer."""
    return np.where(flaked == 1, ASSUMED_FLAKES_PREVENTED * ASSUMED_FLAKE_COST, 0.0) - ASSUMED_VET_COST


# Which pattern warrants a verified-first page: verify a pattern only if verifying
# its hires nets positive under the assumptions (only the Scramble pattern does).
hires["net_if_vetted"] = vet_net(hires["flaked_yes"])
seg_net = hires.groupby("segment")["net_if_vetted"].sum()
VET_SEGMENTS = sorted(seg_net[seg_net > 0].index)

# ------------------------------------------------------------------ decision function
NAMES = {"Segment 1": "Trusted network", "Segment 2": "Open search", "Segment 3": "Scramble"}
DISCOVER_PAGE = {  # page types from our app spec (personalized FYP, reviews, verification)
    "Segment 1": "Past collaborators first: people you have hired before and people they have worked with",
    "Segment 2": "New candidates matched to the role: personalized discovery feed",
    "Segment 3": "Verified, peer-reviewed candidates first",
}
for seg in DISCOVER_PAGE:  # the verified-first page only where the rule says so
    assert ("Verified" in DISCOVER_PAGE[seg]) == (seg in VET_SEGMENTS), seg


def poster_pattern(past_hires):
    """A poster's past hires (rows with ease + search methods) -> their hiring pattern.
    Their hires are averaged and placed at the nearest trained centre."""
    avg = past_hires[FEATURES].astype(float).mean().to_frame().T
    return label[model.predict(scaler.transform(avg))[0]]


def decide(past_hires):
    """Decision for a new job post: the poster's past hires -> (pattern, discover page)."""
    seg = poster_pattern(past_hires)
    return f"{seg} ({NAMES[seg]})", DISCOVER_PAGE[seg]


# ------------------------------------------------------------------ value, baseline vs v1
# Simulate the app on the survey: for each hire, set the poster's page from that
# producer's OTHER hires only (their past pattern), never the hire being judged.
hires["poster_pattern"] = [
    poster_pattern(hires[(hires.producer == r.producer) & (hires.index != i)]) for i, r in hires.iterrows()
]
hires["v1_verified"] = hires["poster_pattern"].isin(VET_SEGMENTS)
v1_net = float(hires.loc[hires.v1_verified, "net_if_vetted"].sum())
base_net = float(hires["net_if_vetted"].sum())
value = {
    "assumptions_FICTIONAL": {"vet_cost": ASSUMED_VET_COST, "flake_cost": ASSUMED_FLAKE_COST,
                              "flakes_prevented": ASSUMED_FLAKES_PREVENTED},
    "segment_net_if_vetted": seg_net.to_dict(),
    "verified_first_patterns": VET_SEGMENTS,
    "baseline_verify_everyone": {"calls_verified": len(hires), "dropouts_covered": int(hires.flaked_yes.sum()),
                                 "net": base_net},
    "v1_by_poster_pattern": {"calls_verified": int(hires.v1_verified.sum()),
                             "dropouts_covered": int(hires.loc[hires.v1_verified, "flaked_yes"].sum()),
                             "net": v1_net},
    "v1_minus_baseline": v1_net - base_net,
    "producer_patterns_all_hires": {int(p): NAMES[poster_pattern(g)] for p, g in hires.groupby("producer")},
}


# ------------------------------------------------------------------ chart
plt.rcParams.update({"font.family": "Arial", "font.size": 13})
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
ks = list(K_RANGE)
ax.plot(ks, [train_sse[k] for k in ks], "o-", color="black", lw=2, label=f"Training ({len(train)} hires)")
ax.axvline(K_CHOSEN, color="#999", lw=1, ls=":")
ax.set_xlabel("Number of groups")
ax.set_ylabel("How much hires differ\nfrom their group (lower = tighter)")
ax.set_xticks(ks)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(f"Built on {len(train)} training hires", fontsize=13, loc="left")
ax.annotate("3 groups: big drop stops here", xy=(K_CHOSEN, train_sse[K_CHOSEN]), xytext=(K_CHOSEN + 0.4, train_sse[2]), fontsize=12, arrowprops=dict(arrowstyle="->"))
fig.tight_layout()
fig.savefig(OUT / "elbow.png")

# ------------------------------------------------------------------ print
r1 = lambda d: {k: round(float(v), 1) for k, v in d.items()}
summary = {
    "hires": len(hires), "producers": int(hires.producer.nunique()),
    "train_n": len(train), "test_n": len(test), "features": FEATURES,
    "train_sse": r1(train_sse),
    "test_sse_baseline_k1": round(float(test_sse[1]), 1), "test_sse_v1": round(float(test_sse[K_CHOSEN]), 1),
    "test_sse_drop_pct_k1_to_k": round(100 * (1 - test_sse[K_CHOSEN] / test_sse[1]), 1),
    "centers": centers.round(2).to_dict(orient="records"),
    "baseline_one_group": baseline,
    "v1_segments": profile.reset_index().to_dict(orient="records"),
    "value": value,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
hires.to_csv(OUT / "hires_segmented.csv", index=False)

print("Elbow, within-segment spread on training hires:")
for k in ks:
    print(f"  k={k}: {train_sse[k]:6.1f}")
print(f"\nTest hires (trained centres, no refit): baseline k=1 {test_sse[1]:.1f}  vs  v1 k={K_CHOSEN} {test_sse[K_CHOSEN]:.1f}")
print(f"\nBaseline (one group): {baseline}\n")
print(profile.T.to_string(), "\n")
print("Value (FICTIONAL ASSUMPTIONS):", json.dumps(value, indent=2), "\n")

# New job post: a poster with a hiring history. Default: producer 6's three past hires.
pid = int(sys.argv[1]) if len(sys.argv) > 1 else 6
history = hires[hires.producer == pid]
print(f"New post by producer {pid}, past hires: {', '.join(history.role)}")
print("  ->", decide(history))
