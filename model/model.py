"""v1 crew-hire segmentation (k-means) on the NYU Student Film Crewing Survey.

Standalone: loads the survey, fits v1, prints the fit evaluation (train and test
elbow), and assigns new hires to a segment.

    python model.py
    python model.py ease=3 "Asking Classmates"=1 "Word-of-mouth / Peer Recommendations"=1

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


hires["net_if_vetted"] = vet_net(hires["flaked_yes"])
seg_net = hires.groupby("segment")["net_if_vetted"].sum()
VET_SEGMENTS = sorted(seg_net[seg_net > 0].index)  # rule: vet a segment if vetting it nets positive
hires["v1_vet"] = hires["segment"].isin(VET_SEGMENTS)
value = {
    "assumptions_FICTIONAL": {"vet_cost": ASSUMED_VET_COST, "flake_cost": ASSUMED_FLAKE_COST,
                              "flakes_prevented": ASSUMED_FLAKES_PREVENTED},
    "segment_net_if_vetted": seg_net.to_dict(),
    "vet_segments": VET_SEGMENTS,
    "baseline_vet_everyone": {"hires_vetted": len(hires), "net": float(hires["net_if_vetted"].sum())},
    "v1_vet_targeted": {"hires_vetted": int(hires.v1_vet.sum()),
                        "net": float(hires.loc[hires.v1_vet, "net_if_vetted"].sum())},
}
value["v1_minus_baseline"] = value["v1_vet_targeted"]["net"] - value["baseline_vet_everyone"]["net"]


# ------------------------------------------------------------------ decision function
def decide(**inputs):
    """One new hire's features (ease + search methods) -> (segment, vet?).
    Missing methods count as not used."""
    x = pd.DataFrame([{f: float(inputs.get(f, 0)) for f in FEATURES}])
    seg = label[model.predict(scaler.transform(x))[0]]
    return seg, seg in VET_SEGMENTS


# ------------------------------------------------------------------ chart
plt.rcParams.update({"font.family": "Arial", "font.size": 13})
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
ks = list(K_RANGE)
ax.plot(ks, [train_sse[k] for k in ks], "o-", color="black", lw=2, label=f"Training ({len(train)} hires)")
ax.plot(ks, [test_sse[k] for k in ks], "s--", color="#777777", lw=2, label=f"Test ({len(test)} hires, trained centres)")
ax.axvline(K_CHOSEN, color="#999", lw=1, ls=":")
ax.set_xlabel("Number of segments (k)")
ax.set_ylabel("Within-segment spread")
ax.set_xticks(ks)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "elbow.png")

# ------------------------------------------------------------------ print
r1 = lambda d: {k: round(float(v), 1) for k, v in d.items()}
summary = {
    "hires": len(hires), "producers": int(hires.producer.nunique()),
    "train_n": len(train), "test_n": len(test), "features": FEATURES,
    "train_sse": r1(train_sse), "test_sse": r1(test_sse),
    "test_sse_drop_pct_k1_to_k": round(100 * (1 - test_sse[K_CHOSEN] / test_sse[1]), 1),
    "centers": centers.round(2).to_dict(orient="records"),
    "baseline_one_group": baseline,
    "v1_segments": profile.reset_index().to_dict(orient="records"),
    "value": value,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
hires.to_csv(OUT / "hires_segmented.csv", index=False)

print("Within-segment spread (train / test):")
for k in ks:
    print(f"  k={k}: {train_sse[k]:6.1f} / {test_sse[k]:6.1f}")
print(f"\nBaseline (one group): {baseline}\n")
print(profile.T.to_string(), "\n")
print("Value (FICTIONAL ASSUMPTIONS):", json.dumps(value, indent=2), "\n")

if len(sys.argv) > 1:  # new hire from the command line
    args = dict(a.split("=", 1) for a in sys.argv[1:])
    print("New hire:", args, "->", decide(**args))
else:  # held-out survey hires as new inputs
    print("Test hires assigned to trained centres:")
    for _, row in test.iterrows():
        seg, vet = decide(**row[FEATURES].to_dict())
        print(f"  {row['role'][:32]:32s} ease={row['ease']:.0f} -> {seg}, vet={vet}")
