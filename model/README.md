# Crewing app: v1 model (k-means clustering)

Run from this folder: `pip install -r requirements.txt`, then `python model.py`, which loads the survey, fits v1, prints the train and test elbow, the segment profiles, and the segment for each held-out hire. Every number is written to `outputs/summary.json`, and the chart to `outputs/elbow.png`.

To assign a new hire: `python model.py ease=3 "Asking Classmates"=1 "Word-of-mouth / Peer Recommendations"=1`

## Data
- Source: NYU Student Film Crewing Survey (Google Form responses, Oct 2026). The repo holds `data/survey_anonymized.xlsx`: names, emails, production titles and free-text answers blanked.
- 10 producers, each reporting up to 3 hires, gives 29 hires (one hire slot was blank). One row per hire.
- Split: 70/30 random (seed 42), giving 20 training hires and 9 test hires.

## Model
- Family: k-means, k = 3. Features standardised on the training rows. No outcome column.
- Features: `ease`, plus a 0/1 flag for each search method used in at least 10 hires (Asking Classmates, Asking Someone You Already Know, Asking Someone You've Worked With, Instagram ISOs, Word-of-mouth / Peer Recommendations).
- Left out: rare methods (Tisch Database, Cold-Emailing, Facebook, WhatsApp, other social, used in 1–3 hires); performance, rehire and flaked (used to describe the segments); names, emails and free-text answers.
- Baseline: one group (k = 1).

## Decision rule and value (FICTIONAL ASSUMPTIONS)
The dollar figures below are **made up for illustration**; they do not come from the survey.
- ASSUMPTION: vetting one hire costs $15.
- ASSUMPTION: a last-minute flake costs a production $300.
- ASSUMPTION: vetting prevents 50% of flakes.

Applied hire by hire using each hire's survey flake answer: a flaked hire nets 0.5 × $300 − $15 = +$135 if vetted, any other hire −$15. Rule: vet a segment if vetting its hires nets positive, which picks Segment 3 only.
- Baseline (vet all 29 hires): +$165
- v1 (vet the 7 hires in Segment 3): +$345, which is $180 better

`decide(...)` returns `(segment, vet?)` for a new hire.

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
| flaked_yes | Did they or anyone else previously hired cancel or flake last minute? (1 = "Yes") |

The raw survey (`data/survey.xlsx`, with names and emails) is git-ignored.
