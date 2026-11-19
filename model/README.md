# Crewing app: v1 model (k-means clustering)

**Business question:** how can we identify distinct crew-hiring patterns to improve recruitment recommendations for student filmmakers?

The model sets the discover page (personalized recommendations) for the person posting a job, based on their past hires.

`python model.py` loads the survey, fits v1, prints the elbow on the training hires, the baseline vs v1 spread on the test hires, the pattern profiles, the value, and the discover page for a new job post. Every number is written to `outputs/summary.json`, and the chart to `outputs/elbow.png`.

To set the discover page for a new post: `python model.py 6` (any producer number 1–10 uses that producer's past hires).

## Data
- Source: NYU Student Film Crewing Survey (Google Form responses collected 14 Oct – 17 Nov 2026, about producers' past productions). The repo holds `data/survey_anonymized.xlsx`: names, emails, production titles and free-text answers blanked.
- 10 producers, each reporting up to 3 hires, gives 29 hires (one hire slot was blank). One row per hire.
- Split: 70/30 random (seed 42), giving 20 training hires and 9 test hires.

## Model
- Family: k-means, k = 3. Features standardised on the training rows. No outcome column.
- Features: a 0/1 flag for each search method used in at least 10 hires (Asking Classmates, Asking Someone You Already Know, Asking Someone You've Worked With, Instagram ISOs, Word-of-mouth / Peer Recommendations). The groups describe **how producers search**.
- Not used to form groups: ease of finding, performance, rehire and dropouts. They describe and check the groups. Also left out: rare methods (Tisch Database, Cold-Emailing, Facebook, WhatsApp, other social, used in 1–3 hires); names, emails and free-text answers.
- k chosen from the elbow on the training hires only: spread 100 → 61 → 34.4 → 26.4 → 19.5 → 13.5. Three groups remove 66%; each extra group after that removes 8 or less.
- Test hires are assigned to the trained centres (no refit): baseline k = 1 spread 50.4 vs v1 k = 3 31.6 (37% lower).
- Check: ease of finding was never an input, yet it differs across the groups (7.3 / 5.1 / 4.1 out of 10; Kruskal-Wallis p = 0.036). How a producer searches predicts how hard the role is to fill.
- Baseline: one group (k = 1), so every filmmaker gets the same discover page.

## What "ease of finding" means
The survey rating (1–10) of how easy it was to find a qualified person for a role, for hires made **before** the app. It varies by role scarcity and by whether the producer has a network. v2 replaces it with the app's own data: applicants per post, days to fill, re-book rate.

## How the app uses it
When someone posts a job, the search methods of their **past hires** are averaged and placed at the nearest trained centre. That hiring pattern sets their discover page:

| Poster's pattern | Discover page | Producers in survey | Shortlist saves per post |
|---|---|---|---|
| Segment 1: Trusted network | Re-book page: past collaborators first | 3 of 10 | 1.4 hours |
| Segment 2: Open search | Discovery feed of new candidates matched to the role | 4 of 10 | 2.5 hours |
| Segment 3: Scramble | Curated shortlist first, then the discovery feed | 3 of 10 | 2.9 hours |

`decide(past_hires)` returns `(pattern, discover page, curated shortlist?)`. `python model.py 6` runs it for producer 6 (DP, UPM, art director: Scramble).

## Value (FICTIONAL ASSUMPTIONS)
The hour and dollar figures are **made up for illustration** and were fixed before computing results.
- ASSUMPTION: a role takes 1 hour of searching per point of difficulty (10 − ease).
- ASSUMPTION: a curated shortlist halves search time.
- ASSUMPTION: a producer hour is worth $20.
- ASSUMPTION: a shortlist costs the app $25.

Net value per post = hours saved × $20 − shortlist cost. Open search and Scramble hold 76% of all search hours (96 of 126). A pattern gets shortlists only while they pay for themselves: Trusted network up to $27 a post, Open search up to $49, Scramble up to $59. To test fairly, each hire's page is set only from that producer's **other** hires.

| Shortlist cost | Plan | Shortlists | Hours saved | Net |
|---|---|---|---|---|
| $25 (base case) | Baseline: everyone | 29 | 63 | +$535 |
| $25 (base case) | v1: by poster's pattern | 29 | 63 | +$535 |
| $40 (what-if) | Baseline: everyone | 29 | 63 | +$100 |
| $40 (what-if) | v1: by poster's pattern | 18 | 43 | +$140 |

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
