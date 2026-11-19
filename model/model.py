"""v1 crew-hiring patterns (k-means) on the NYU Student Film Crewing Survey.

Business question: how can we identify distinct crew-hiring patterns to improve
recruitment recommendations for student filmmakers?

Use: when someone posts a job, their past hires place them in a hiring pattern,
and the pattern sets their discover page (personalized recommendations).

Groups are formed from HOW producers searched (5 search methods). Ease of finding
(1-10) is NOT used to form groups; it is the outcome the groups are checked
against, together with ratings, rehire and dropouts.

Standalone: loads the survey, fits v1, prints the fit evaluation (elbow on all
29 hires; fewer than 30, so no train/test split), and returns the
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

# Fewer than 30 hires (29), so per the assignment there is no train/test split:
# the scaling and the groups are fitted on all 29 hires.
scaler = StandardScaler().fit(hires[FEATURES])
X_all = scaler.transform(hires[FEATURES])

# ------------------------------------------------------------------ fit k = 1..6
models, sse = {}, {}
for k in K_RANGE:
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(X_all)
    models[k] = km
    sse[k] = km.inertia_
model = models[K_CHOSEN]

hires["cluster"] = model.predict(scaler.transform(hires[FEATURES]))
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


# ------------------------------------------------------------------ decision function
# Every poster gets recommendations; the TYPE depends on their hiring pattern.
RECOMMENDATIONS = {
    "Segment 1": "Re-book: people they have worked with, and people those crew members recommend",
    "Segment 2": "Feed of new people who fit the role",
    "Segment 3": "Hand-picked shortlist of available, reviewed people",
}


def decide(past_hires):
    """New job post: the poster's past hires -> (pattern, recommendations they get)."""
    seg = poster_pattern(past_hires)
    return f"{seg} ({NAMES[seg]})", RECOMMENDATIONS[seg]


# ------------------------------------------------------------------ value: FICTIONAL ASSUMPTIONS
# None of these figures come from the survey; they must be labelled as assumptions.
ASSUMED_HOURS_PER_POINT = 1.0   # ASSUMPTION: search hours = 1 x (10 - ease); a role rated 2 takes 8 hours
ASSUMED_GENERIC_CUT = 0.25      # ASSUMPTION: the same generic feed for everyone cuts search time by 25%
ASSUMED_MATCHED_CUT = 0.50      # ASSUMPTION: recommendations matched to the poster's pattern cut it by 50%

hires["search_hours"] = ASSUMED_HOURS_PER_POINT * (10 - hires["ease"])
example = hires[(hires.producer == 6) & (hires.role == "Art Director")].iloc[0]
value = {
    "assumptions_FICTIONAL": {"hours_per_difficulty_point": ASSUMED_HOURS_PER_POINT,
                              "generic_feed_cut": ASSUMED_GENERIC_CUT, "matched_cut": ASSUMED_MATCHED_CUT},
    "search_hours_total": float(hires["search_hours"].sum()),
    "baseline_same_feed_hours_saved": float(ASSUMED_GENERIC_CUT * hires["search_hours"].sum()),
    "v1_matched_hours_saved": float(ASSUMED_MATCHED_CUT * hires["search_hours"].sum()),
    "example": {"producer": 6, "role": example.role, "ease": float(example.ease),
                "search_hours": float(example.search_hours),
                "generic_saves": ASSUMED_GENERIC_CUT * float(example.search_hours),
                "matched_saves": ASSUMED_MATCHED_CUT * float(example.search_hours)},
    "producer_patterns": {int(p): NAMES[poster_pattern(g)] for p, g in hires.groupby("producer")},
}

# ------------------------------------------------------------------ chart
plt.rcParams.update({"font.family": "Arial", "font.size": 13})
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
ks = list(K_RANGE)
ax.plot(ks, [sse[k] for k in ks], "o-", color="black", lw=2)
ax.axvline(K_CHOSEN, color="#999", lw=1, ls=":")
ax.set_xlabel("Number of groups")
ax.set_ylabel("How much hires differ\nfrom their group (lower = tighter)")
ax.set_xticks(ks)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(f"Built on all {len(hires)} hires", fontsize=13, loc="left")
ax.annotate("3 groups: big drop stops here", xy=(K_CHOSEN, sse[K_CHOSEN]),
            xytext=(K_CHOSEN + 0.4, sse[2]), fontsize=12, arrowprops=dict(arrowstyle="->"))
fig.tight_layout()
fig.savefig(OUT / "elbow.png")

# ------------------------------------------------------------------ print
r1 = lambda d: {k: round(float(v), 1) for k, v in d.items()}
summary = {
    "hires": len(hires), "producers": int(hires.producer.nunique()),
    "split": "none (29 hires < 30): fitted on all hires", "features": FEATURES,
    "sse": r1(sse), "sse_drop_pct_k1_to_k": round(100 * (1 - sse[K_CHOSEN] / sse[1]), 1),
    "centers": centers.round(2).to_dict(orient="records"),
    "baseline_one_group": baseline,
    "v1_segments": profile.reset_index().to_dict(orient="records"),
    "value": value,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
hires.to_csv(OUT / "hires_segmented.csv", index=False)

print("Elbow, within-group spread on all 29 hires:")
for k in ks:
    print(f"  k={k}: {sse[k]:6.1f}")
print(f"\nBaseline k=1 {sse[1]:.1f}  vs  v1 k={K_CHOSEN} {sse[K_CHOSEN]:.1f}")
print(f"\nBaseline (one group): {baseline}\n")
print(profile.T.to_string(), "\n")
print("Value (FICTIONAL ASSUMPTIONS):", json.dumps(value, indent=2), "\n")

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 6
history = hires[hires.producer == pid]
print(f"New post by producer {pid}, past hires: {', '.join(history.role)}")
print("  ->", decide(history))
