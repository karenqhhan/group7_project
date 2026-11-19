"""v1 crew-hiring patterns (k-means) on the NYU Student Film Crewing Survey.

Business question: how can we identify distinct crew-hiring patterns to improve
recruitment recommendations for student filmmakers?

Use: when someone posts a job, their past hires place them in a hiring pattern,
and the pattern sets their discover page (personalized recommendations).

Groups are formed from HOW producers searched (5 search methods). Ease of finding
(1-10) is NOT used to form groups; it is the outcome the groups are checked
against, together with ratings, rehire and dropouts.

Standalone: loads the survey, fits v1, prints the fit evaluation (elbow on the
training hires; baseline vs v1 spread on the test hires), and returns the
discover page for a new job post.

    python model.py          # new post by producer 6, using their past hires
    python model.py 9        # same for producer 9

Model fit uses only survey fields. Dollar and hour figures in the value section are
FICTIONAL ASSUMPTIONS.
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
OUTCOMES = ["ease", "performance", "rehire_yes", "flaked_yes"]

# ------------------------------------------------------------------ data + split
hires = load(HERE / "data" / "survey_anonymized.xlsx")
hires.to_csv(OUT / "hires_clean.csv", index=False)

# Features: each search method used in at least 10 of the 29 hires (rarer methods,
# used 1-3 times, are too rare to define a group). Everything else describes the groups.
FEATURES = [m for m in METHODS if hires[m].sum() >= 10]

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

hires["cluster"] = model.predict(scaler.transform(hires[FEATURES]))
hires["set"] = np.where(hires.index.isin(train.index), "train", "test")
# Label segments 1..k by average ease of their hires, easiest first.
order = hires.groupby("cluster")["ease"].mean().sort_values(ascending=False).index
label = {c: f"Segment {i + 1}" for i, c in enumerate(order)}
hires["segment"] = hires["cluster"].map(label)
centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=FEATURES)
centers["segment"] = centers.index.map(label)

NAMES = {"Segment 1": "Trusted network", "Segment 2": "Open search", "Segment 3": "Scramble"}
baseline = hires[OUTCOMES].mean().round(3).to_dict() | {"hires": len(hires)}
profile = hires.groupby("segment").agg(
    hires=("role", "size"), **{f: (f, "mean") for f in FEATURES + OUTCOMES}
).round(2)


# ------------------------------------------------------------------ poster's pattern
def poster_pattern(past_hires):
    """A poster's past hires (search methods used) -> their hiring pattern.
    Their hires are averaged and placed at the nearest trained centre."""
    avg = past_hires[FEATURES].astype(float).mean().to_frame().T
    return label[model.predict(scaler.transform(avg))[0]]


# ------------------------------------------------------------------ value: FICTIONAL ASSUMPTIONS
# None of these figures come from the survey. They were fixed before computing results
# and must be labelled as assumptions on the slides.
ASSUMED_HOURS_PER_POINT = 1.0    # ASSUMPTION: search hours = 1 x (10 - ease); ease 10 = no search
ASSUMED_SHORTLIST_CUT = 0.5      # ASSUMPTION: a curated shortlist halves search time
ASSUMED_HOUR_VALUE = 20.0        # ASSUMPTION: $ value of one producer hour
ASSUMED_SHORTLIST_COST = 25.0    # ASSUMPTION: $ cost to the app of one curated shortlist

hires["search_hours"] = ASSUMED_HOURS_PER_POINT * (10 - hires["ease"])
hires["hours_saved"] = ASSUMED_SHORTLIST_CUT * hires["search_hours"]


def pattern_gets_shortlist(cost):
    """Patterns where shortlists pay for themselves at this cost (summed over their hires)."""
    net = (hires["hours_saved"] * ASSUMED_HOUR_VALUE - cost).groupby(hires["segment"]).sum()
    return sorted(net[net > 0].index)


# Cost at which each pattern stops paying off: hours saved x hour value / hires.
breakeven = (hires.groupby("segment")["hours_saved"].mean() * ASSUMED_HOUR_VALUE).round(2).to_dict()

# Simulate the app on the survey: each hire's page is set from that producer's OTHER
# hires only (their past pattern), never the hire being judged.
hires["poster_pattern"] = [
    poster_pattern(hires[(hires.producer == r.producer) & (hires.index != i)]) for i, r in hires.iterrows()
]


def plan(cost, targeted):
    gets = hires["poster_pattern"].isin(pattern_gets_shortlist(cost)) if targeted else pd.Series(True, hires.index)
    sub = hires[gets]
    return {"shortlists": int(gets.sum()), "hours_saved": float(sub.hours_saved.sum()),
            "net": float((sub.hours_saved * ASSUMED_HOUR_VALUE - cost).sum())}


SCENARIO_COSTS = [ASSUMED_SHORTLIST_COST, 40.0]  # base case plus a higher-cost what-if
value = {
    "assumptions_FICTIONAL": {"hours_per_difficulty_point": ASSUMED_HOURS_PER_POINT,
                              "shortlist_cut": ASSUMED_SHORTLIST_CUT, "hour_value": ASSUMED_HOUR_VALUE,
                              "shortlist_cost": ASSUMED_SHORTLIST_COST},
    "search_hours_by_pattern": hires.groupby("segment")["search_hours"].sum().to_dict(),
    "search_hours_total": float(hires["search_hours"].sum()),
    "hours_saved_per_post": hires.groupby("segment")["hours_saved"].mean().round(2).to_dict(),
    "breakeven_shortlist_cost": breakeven,
    "scenarios": {str(c): {"patterns_with_shortlist": pattern_gets_shortlist(c),
                           "baseline_everyone": plan(c, False), "v1_by_pattern": plan(c, True)}
                  for c in SCENARIO_COSTS},
    "producer_patterns": {int(p): NAMES[poster_pattern(g)] for p, g in hires.groupby("producer")},
}

# ------------------------------------------------------------------ decision function
DISCOVER_PAGE = {
    "Segment 1": "Re-book page: past collaborators first, then people they have worked with",
    "Segment 2": "Discovery feed: new candidates matched to the role",
    "Segment 3": "Curated shortlist first: hand-picked available candidates, then the discovery feed",
}


def decide(past_hires, shortlist_cost=ASSUMED_SHORTLIST_COST):
    """New job post: the poster's past hires -> (pattern, discover page, curated shortlist?)."""
    seg = poster_pattern(past_hires)
    return f"{seg} ({NAMES[seg]})", DISCOVER_PAGE[seg], seg in pattern_gets_shortlist(shortlist_cost)


# ------------------------------------------------------------------ chart
plt.rcParams.update({"font.family": "Arial", "font.size": 13})
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
ks = list(K_RANGE)
ax.plot(ks, [train_sse[k] for k in ks], "o-", color="black", lw=2)
ax.axvline(K_CHOSEN, color="#999", lw=1, ls=":")
ax.set_xlabel("Number of groups")
ax.set_ylabel("How much hires differ\nfrom their group (lower = tighter)")
ax.set_xticks(ks)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(f"Built on {len(train)} training hires", fontsize=13, loc="left")
ax.annotate("3 groups: big drop stops here", xy=(K_CHOSEN, train_sse[K_CHOSEN]),
            xytext=(K_CHOSEN + 0.4, train_sse[2]), fontsize=12, arrowprops=dict(arrowstyle="->"))
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

print("Elbow, within-group spread on training hires:")
for k in ks:
    print(f"  k={k}: {train_sse[k]:6.1f}")
print(f"\nTest hires (trained centres, no refit): baseline k=1 {test_sse[1]:.1f}  vs  v1 k={K_CHOSEN} {test_sse[K_CHOSEN]:.1f}")
print(f"\nBaseline (one group): {baseline}\n")
print(profile.T.to_string(), "\n")
print("Value (FICTIONAL ASSUMPTIONS):", json.dumps(value, indent=2), "\n")

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 6
history = hires[hires.producer == pid]
print(f"New post by producer {pid}, past hires: {', '.join(history.role)}")
print("  ->", decide(history))
