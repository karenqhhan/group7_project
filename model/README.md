# Crewing app: v1 model (k-means clustering)

**Business question:** how can we identify distinct crew-hiring patterns to improve recruitment recommendations for student filmmakers?

The model sets the discover page (personalized recommendations) for the person posting a job, based on their past hires.

`python model.py` loads the survey, fits v1, prints the elbow on all 29 hires, the baseline vs v1 spread, the pattern profiles, the value, and the discover page for a new job post. Every number is written to `outputs/summary.json`, and the chart to `outputs/elbow.png`.

To set the discover page for a new post: `python model.py 6` (any producer number 1–10 uses that producer's past hires).

## Data
- Source: NYU Student Film Crewing Survey (Google Form responses collected 14 Oct – 17 Nov 2026, about producers' past productions). The repo holds `data/survey_anonymized.xlsx`: names, emails, production titles and free-text answers blanked.
- 10 producers, each reporting up to 3 hires, gives 29 hires (one hire slot was blank). One row per hire.
- No train/test split: with 29 hires (fewer than 30), the assignment says to fit on the whole data set.

## Model
- Family: k-means, k = 3. Features standardised on all 29 hires. No outcome column.
- Features: a 0/1 flag for each search method used in at least 10 hires (Asking Classmates, Asking Someone You Already Know, Asking Someone You've Worked With, Instagram ISOs, Word-of-mouth / Peer Recommendations). The groups describe **how producers search**.
- Not used to form groups: ease of finding, performance, rehire and dropouts. They describe and check the groups. Also left out: rare methods (Tisch Database, Cold-Emailing, Facebook, WhatsApp, other social, used in 1–3 hires); names, emails and free-text answers.
- k chosen from the elbow on all 29 hires: spread 145 → 92.7 → 60.1 → 47.1 → 36.3 → 28.4. Three groups remove 59% of the spread compared with one group (baseline); each extra group after that removes 13 or less.
- Check: ease of finding was never an input, yet it differs across the groups (7.3 / 5.1 / 4.1 out of 10; Kruskal-Wallis p = 0.036). How a producer searches predicts how hard the role is to fill.
- Baseline: one group (k = 1), so every filmmaker gets the same discover page.

## What "ease of finding" means
The survey rating (1–10) of how easy it was to find a qualified person for a role, for hires made **before** the app. It varies by role scarcity and by whether the producer has a network. v2 replaces it with the app's own data: applicants per post, days to fill, re-book rate.

## How the app uses it
Every poster gets recommendations; the **type** depends on their hiring pattern. When someone posts a job, the search methods of their past hires are averaged and placed at the nearest trained centre:

| Poster's pattern | Recommendations | Producers in survey |
|---|---|---|
| Segment 1: Trusted network | Re-book: people they have worked with, and people those crew members recommend | 3 of 10 |
| Segment 2: Open search | A feed of new people who fit the role | 4 of 10 |
| Segment 3: Scramble | A hand-picked shortlist of available, reviewed people | 3 of 10 |

`decide(past_hires)` returns `(pattern, recommendations)`. `python model.py 6` runs it for producer 6 (DP, UPM, art director: Scramble).

## Value (FICTIONAL ASSUMPTIONS)
The hour figures are **made up for illustration**.
- ASSUMPTION: a role takes 1 hour of searching per point of difficulty (10 − ease); a role rated 2 takes 8 hours.
- ASSUMPTION: the same generic feed for everyone (baseline) cuts search time by 25%.
- ASSUMPTION: recommendations matched to the poster's pattern (v1) cut it by 50%.

Example: producer 6's art director (rated 2 out of 10) takes 8 hours with no help, 6 with the generic feed, 4 with a matched shortlist. Across all 29 hires (126 search hours): baseline saves 31.5 hours, v1 saves 63.

## Data dictionary (`outputs/hires_clean.csv`)
| Column | Survey question |
|---|---|
| producer | respondent number (anonymised) |
| slot | hire 1–3 for that producer |
| project_type | What was this project for? |
| role | Which role did you hire for this production? |
| ease | How easy was it to find a qualified candidate? (1–10) |
| one column per method | What method do you use to find crew? (1 = selected) |
| performance | How well did the person perform? (1–10) |
| rehire_yes | Would you hire/work with this person again? (1 = "Yes"; any other answer = 0) |
| flaked_yes | Did they **or anyone else previously hired for this role** cancel or flake within 24–48h of call time? (1 = "Yes"). A role-level dropout, not necessarily the person hired. |

The raw survey (`data/survey.xlsx`, with names and emails) is git-ignored.
