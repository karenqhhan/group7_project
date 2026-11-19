const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
const K = "000000";
const X = 0.7, W = 11.93;
const box = { isTextBox: true, margin: 0, valign: "top", color: K };
const title = (s, t) => s.addText(t, { ...box, x: X, y: 0.45, w: W, h: 1.0, fontSize: 25, bold: true });
const text = (s, t, o) => s.addText(t, { ...box, fontSize: 12, ...o });
const list = (items, o = {}) => items.map((t, i) => ({ text: t, options: { bullet: o.num ? { type: "number" } : true, breakLine: i < items.length - 1 } }));
const B = { type: "solid", pt: 0.75, color: K }, N = { type: "none" };
const cell = (t, bold = false) => ({ text: t, options: { bold, border: [N, N, B, N] } });
const table = (s, rows, o) => s.addTable(rows, { fontSize: 12, color: K, fontFace: "Arial", margin: [3, 5, 3, 5], ...o });

// ---------------------------------------------------------------- 1 Title
let s = pres.addSlide();
s.addText("How can we identify distinct crew-hiring patterns to improve recruitment recommendations for student filmmakers?",
  { ...box, x: X, y: 1.8, w: W, h: 2.0, fontSize: 30, bold: true });
s.addText(list(["[Team name]", "[Members]", "github.com/karenqhhan/group7_project · model script: model/model.py"]).map(r => ({ ...r, options: { ...r.options, bullet: false } })),
  { ...box, x: X, y: 4.0, w: W, h: 1.3, fontSize: 16, paraSpaceAfter: 6 });

// ---------------------------------------------------------------- 2 Patterns
s = pres.addSlide();
title(s, "Student filmmakers hire crew in three distinct ways, and one of them accounts for 3 of the 4 last-minute dropouts");
const segs = [["1 · Trusted network", "11 hires · 3 of 10 producers mostly hire this way", "“I already know who to call.”", ["How they hire: 91% were found by asking someone the producer already knew; mostly key roles (DPs, ADs, 1st ACs)", "Results: easy to fill (7.4 out of 10, where 10 = very easy); hires rated 9.5 out of 10; 91% would hire them again; 1 of 11 roles had a last-minute dropout"]], ["2 · Open search", "11 hires · 5 of 10 producers", "“I need someone new.”", ["How they hire: about 3 in 4 posted Instagram ISOs, and about 3 in 4 asked for referrals; only 1 in 11 asked someone they already knew; specialist and support roles (art, gaffer, grip, colorist, makeup)", "Results: moderately hard to fill (5.1 out of 10); hires rated 7.5 out of 10; 82% would hire again; no dropouts"]], ["3 · Scramble", "7 hires · 2 of 10 producers", "“I’m trying everything.”", ["How they hire: every channel at once (all asked classmates, people they knew and for referrals); mostly senior and advanced productions", "Results: hardest to fill (3.9 out of 10); hires rated 7.4 out of 10; only 57% would hire again; 3 of 7 roles had a last-minute dropout"]]];
const HW = 5.9, bh = 1.75, bgap = 0.1;
segs.forEach(([h, sub, q, items], i) => {
  const y = 1.5 + i * (bh + bgap);
  s.addShape(pres.shapes.RECTANGLE, { x: X, y, w: HW, h: bh, fill: { color: "FFFFFF" }, line: { color: K, width: 0.75 } });
  text(s, [{ text: h + " ", options: { bold: true, fontSize: 13 } }, { text: "(" + sub + ") " }, { text: q, options: { italic: true } }], { x: X + 0.12, y: y + 0.07, w: HW - 0.24, h: 0.45 });
  text(s, list(items), { x: X + 0.12, y: y + 0.52, w: HW - 0.24, h: bh - 0.56, fontSize: 11.5, paraSpaceAfter: 3 });
});
const PX = X + HW + 0.4, PW = W - HW - 0.4, CW = PW * 0.88;
text(s, "Proof: the three patterns are real", { x: PX, y: 1.5, w: PW, h: 0.3, fontSize: 14, bold: true });
s.addImage({ path: path.join(__dirname, "../outputs/elbow.png"), x: PX, y: 1.82, w: CW, h: CW * 4 / 6.5, altText: "Chart: how much hires differ from their group, by number of groups" });
text(s, [["How the groups were found: ", "a clustering model (k-means) sorted the hires into groups of similar hires, using only what is known before hiring: how hard the role was to fill and which search methods were used. Results (ratings, dropouts) were left out, so they are a fair check on the groups."], ["Why three groups: ", "the chart shows how much hires still differ from their group (lower = tighter groups). Three groups cut that from 120 to 46, a 62% drop; each group after that helps by 10 or less, so three is where splitting stops paying off."], ["Does it hold for new hires? ", "We hid 9 of the 29 hires (about 30%) while building the groups, then sorted them in afterwards. Three groups described them 25% better than one group for everyone (56.7 → 42.4)."], ["Data: ", "our NYU Student Film Crewing Survey, answered Oct–Nov 2026 about past productions: 10 producers, 29 hires."]].map(([b, t], i, arr) => [
  { text: b, options: { bold: true, bullet: true } }, { text: t, options: { breakLine: i < arr.length - 1 } }]).flat(),
  { x: PX, y: 1.88 + CW * 4 / 6.5, w: PW, h: 7.15 - (1.88 + CW * 4 / 6.5), fontSize: 10, paraSpaceAfter: 2 });

// ---------------------------------------------------------------- 3 Personalization + value
s = pres.addSlide();
title(s, "Building each poster’s discover page from their past hires covers half the dropouts with 72% fewer verifications");
const LW = 4.6, RX = X + LW + 0.35, RW = W - LW - 0.35;
text(s, "How personalization works", { x: X, y: 1.55, w: LW, h: 0.3, fontSize: 14, bold: true });
text(s, list([
  "A filmmaker posts a job",
  "The app looks at their past hires (how hard each role was to fill, how they searched) and places them in their closest hiring pattern",
  "Their discover page is built for that pattern",
], { num: true }), { x: X, y: 1.9, w: LW, h: 1.55, paraSpaceAfter: 4 });
text(s, "Example", { x: X, y: 3.45, w: LW, h: 0.3, fontSize: 14, bold: true });
text(s, "Producer 6 posts a job. Past hires: DP, UPM, art director, all hard to fill (1–3 out of 10), found through people they know, classmates and referrals → Scramble → verified, peer-reviewed candidates first",
  { x: X, y: 3.77, w: LW, h: 0.95 });
table(s, [
  [cell("Poster’s pattern", true), cell("Their discover page shows", true), cell("Why", true)],
  [cell("1 · Trusted network"), cell("Past collaborators first, and people they have worked with"), cell("They hire who they know, and those hires perform best")],
  [cell("2 · Open search"), cell("New candidates matched to the role"), cell("They need new people, and strangers found this way were reliable")],
  [cell("3 · Scramble"), cell("Verified, peer-reviewed candidates first", true), cell("Hardest roles with the most last-minute dropouts; verification is worth its cost only here")],
], { x: RX, y: 1.55, w: RW, colW: [1.7, 2.4, RW - 4.1] });
text(s, "What it is worth (29 surveyed hires)", { x: X, y: 4.85, w: LW, h: 0.3, fontSize: 14, bold: true });
text(s, "How we tested it: we treated each hire as a new job post and set the page using only that producer’s other hires, so the model never saw the answer. Checking every post finds all 4 dropouts but pays for 29 checks; personalizing pays for 8 checks, finds 2, and still comes out $15 ahead.", { x: X, y: 5.18, w: LW, h: 1.3, fontSize: 11.5 });
table(s, [
  [cell("Plan", true), cell("Calls verified", true), cell("Dropouts covered", true), cell("Net value (savings − cost)", true)],
  [cell("Baseline: same page for every poster"), cell("29"), cell("4 of 4"), cell("+$165")],
  [cell("v1: page by poster’s past pattern"), cell("8"), cell("2 of 4"), cell("+$180", true)],
], { x: RX, y: 4.85, w: RW, colW: [RW - 4.6, 1.3, 1.5, 1.8] });
text(s, "How the dollars work (fictional assumptions): each verification check costs $15. A last-minute dropout costs a production $300, and checking prevents half of them, so checking a role that would have had a dropout saves $150 − $15 = $135, and checking any other role just costs $15. Baseline: 4 × $135 − 25 × $15 = +$165. v1: 2 × $135 − 6 × $15 = +$180.",
  { x: X, y: 6.5, w: W, h: 0.65, fontSize: 10 });

pres.writeFile({ fileName: path.join(__dirname, "group7_model_slides.pptx") }).then(f => console.log("wrote", f));
