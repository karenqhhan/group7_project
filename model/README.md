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
- Features: `ease`, plus a 0/1 flag for each search method used in at least 10 hires (Asking Classmates, Asking Someone You Already Know, Asking Someone You've Worked With, Instagram ISOs, Word-of-mouth / Peer Recommendations).
- Left out: rare methods (Tisch Database, Cold-Emailing, Facebook, WhatsApp, other social, used in 1–3 hires); performance, rehire and dropout (used to describe the segments); names, emails and free-text answers.
- k chosen from the elbow on the training hires only: spread drops 46.5, then 27.5, then 10 or less per extra group, so it flattens after 3. The elbow is soft (an automatic second-difference rule narrowly prefers 2); 3 was chosen because 2 → 3 still removes 23% of the total spread. Test hires are assigned to the trained centres (no refit) to compare spread: baseline k = 1 56.7 vs v1 k = 3 42.4.
- Baseline: one group (k = 1), so every filmmaker gets the same recommendations.

## How the app uses it
When someone posts a job, their **past hires** (ease of finding + search methods) are averaged and placed at the nearest trained centre. That hiring pattern sets their discover page:

| Poster's pattern | Discover page | Producers in survey |
|---|---|---|
| Segment 1: Trusted network | Past collaborators first, and people they have worked with | 3 of 10 |
| Segment 2: Open search | New candidates matched to the role | 5 of 10 |
| Segment 3: Scramble | Verified, peer-reviewed candidates first | 2 of 10 |

`decide(past_hires)` returns `(pattern, discover page)`. `python model.py 6` runs it for producer 6 (DP, UPM, art director: Scramble).

The verified-first page goes only to a pattern where verifying its hires nets positive under the assumptions below (only Scramble).

## Value (FICTIONAL ASSUMPTIONS)
The dollar figures are **made up for illustration**; they do not come from the survey.
- ASSUMPTION: verifying a call costs $15.
- ASSUMPTION: a last-minute dropout costs a production $300.
- ASSUMPTION: verification prevents 50% of dropouts.

Applied role by role using the survey's dropout answer: a role with a dropout nets 0.5 × $300 − $15 = +$135 if verified, any other −$15. To test fairly, each hire's page is set only from that producer's **other** hires.
- Baseline (same page for every poster, every call verified): 29 calls, 4 of 4 dropouts covered, +$165
- v1 (page by poster's past pattern): 8 calls verified, 2 of 4 dropouts covered, +$180 (+$15, with 72% fewer verifications)

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
