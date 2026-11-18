"""Reshape the survey (one row per producer, 3 hires each) to one row per hire.

Only fields from the survey are used. Names, emails and free-text answers are dropped.
"""
import pandas as pd

# Search methods as worded in the survey's multi-select question.
METHODS = [
    "Asking Classmates",
    "Asking Someone You Already Know",
    "Asking Someone You've Worked With",
    "Cold-Emailing / Pitching",
    "Facebook Groups",
    'Instagram ISOs ("In Search Of")',
    "Other Social Medias (e.g., TikTok, Reddit)",
    "Using the Tisch Database",
    "WhatsApp group chats",
    "Word-of-mouth / Peer Recommendations",
]


def load(path):
    d = pd.read_excel(path)
    c = list(d.columns)
    rows = []
    for slot, off in enumerate([10, 20, 30], start=1):  # the three hire blocks in the form
        for i, r in d.iterrows():
            rows.append(dict(
                producer=i + 1, slot=slot, project_type=r[c[7]], role=str(r[c[off]]).strip(),
                method=str(r[c[off + 1]]), ease=r[c[off + 4]], performance=r[c[off + 5]],
                rehire=r[c[off + 6]], flaked=r[c[off + 8]],
            ))
    h = pd.DataFrame(rows)
    h = h[h.role.str.lower() != "na"].reset_index(drop=True)  # one hire slot left blank
    h["ease"] = h.ease.astype(float)
    h["performance"] = h.performance.astype(float)
    for m in METHODS:
        h[m] = h.method.str.contains(m, regex=False).astype(int)
    h["rehire_yes"] = (h.rehire == "Yes").astype(int)
    h["flaked_yes"] = (h.flaked == "Yes").astype(int)
    return h.drop(columns=["method"])
