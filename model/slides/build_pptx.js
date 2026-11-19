// Build group7_model_slides.pptx from content.json (same text as slides.html).
const pptxgen = require("pptxgenjs");
const path = require("path");
const C = require("./content.json");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
const K = "000000";
const X = 0.7, W = 11.93;
const box = { isTextBox: true, margin: 0, valign: "top", color: K };
const title = (s, t) => s.addText(t, { ...box, x: X, y: 0.4, w: W, h: 0.95, fontSize: 23, bold: true });
const text = (s, t, o) => s.addText(t, { ...box, fontSize: 11, ...o });
const list = (items, num = false) => items.map((t, i) => ({ text: t, options: { bullet: num ? { type: "number" } : true, breakLine: i < items.length - 1 } }));
const B = { type: "solid", pt: 0.75, color: K }, N = { type: "none" };
const cell = (t, bold = false) => ({ text: t, options: { bold, border: [N, N, B, N] } });
const table = (s, head, body, o) => s.addTable([head.map(h => cell(h, true)), ...body.map(r => r.map(c => cell(c)))],
  { fontSize: 11, color: K, fontFace: "Arial", margin: [2, 4, 2, 4], ...o });

// ---------------------------------------------------------------- 1 Title
let s;
if (!process.env.ONLY3) {
s = pres.addSlide();
s.addText(C.title, { ...box, x: X, y: 1.8, w: W, h: 2.0, fontSize: 30, bold: true });
s.addText(C.title_lines.map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })),
  { ...box, x: X, y: 4.0, w: W, h: 1.3, fontSize: 16, paraSpaceAfter: 6 });

// ---------------------------------------------------------------- 2 Patterns + proof
s = pres.addSlide();
title(s, C.s2_title);
const HW = 5.9, bh = 1.78, bgap = 0.1;
C.segs.forEach(([h, sub, q, items], i) => {
  const y = 1.42 + i * (bh + bgap);
  s.addShape(pres.shapes.RECTANGLE, { x: X, y, w: HW, h: bh, fill: { color: "FFFFFF" }, line: { color: K, width: 0.75 } });
  text(s, [{ text: h + " ", options: { bold: true, fontSize: 13 } }, { text: "(" + sub + ") " }, { text: q, options: { italic: true } }],
    { x: X + 0.12, y: y + 0.06, w: HW - 0.24, h: 0.3 });
  text(s, list(items), { x: X + 0.12, y: y + 0.38, w: HW - 0.24, h: bh - 0.42, paraSpaceAfter: 2 });
});
const PX = X + HW + 0.4, PW = W - HW - 0.4, CW = PW * 0.8, CH = CW * 4 / 6.5;
text(s, C.proof_title, { x: PX, y: 1.42, w: PW, h: 0.28, fontSize: 13, bold: true });
s.addImage({ path: path.join(__dirname, "../outputs/elbow.png"), x: PX, y: 1.72, w: CW, h: CH, altText: "Chart: how much hires differ from their group, by number of groups" });
text(s, C.proof.map(([b, t], i, a) => [
  { text: b, options: { bold: true, bullet: true } }, { text: t, options: { breakLine: i < a.length - 1 } }]).flat(),
  { x: PX, y: 1.78 + CH, w: PW, h: 7.15 - (1.78 + CH), fontSize: 9.5, paraSpaceAfter: 2 });

}
// ---------------------------------------------------------------- 3 Recommendations + value
s = pres.addSlide();
title(s, C.s3_title);
const LW = 6.6, RX = X + LW + 0.45, RW = W - LW - 0.45;
table(s, C.recs_head, C.recs, { x: X, y: 1.5, w: LW, colW: [1.7, 2.2, LW - 3.9], fontSize: 13, margin: [4, 5, 4, 5] });
text(s, C.how_line, { x: X, y: 4.3, w: LW, h: 0.7, fontSize: 13 });
s.addShape(pres.shapes.RECTANGLE, { x: RX, y: 1.5, w: RW, h: 2.55, fill: { color: "FFFFFF" }, line: { color: K, width: 0.75 } });
text(s, C.ex_title, { x: RX + 0.15, y: 1.6, w: RW - 0.3, h: 0.3, fontSize: 13, bold: true });
text(s, C.ex_intro, { x: RX + 0.15, y: 1.92, w: RW - 0.3, h: 0.5 });
table(s, C.ex_head, C.ex_rows, { x: RX + 0.15, y: 2.45, w: RW - 0.3, colW: [RW - 2.4, 2.1], fontSize: 13, margin: [4, 5, 4, 5] });
text(s, C.tot_title, { x: RX, y: 4.3, w: RW, h: 0.3, fontSize: 13, bold: true });
table(s, C.tot_head, C.tot_rows, { x: RX, y: 4.65, w: RW, colW: [RW - 1.9, 1.9], fontSize: 13, margin: [4, 5, 4, 5] });
text(s, C.foot, { x: X, y: 6.6, w: W, h: 0.5, fontSize: 10 });

pres.writeFile({ fileName: path.join(__dirname, process.env.ONLY3 ? "slide3.pptx" : "group7_model_slides.pptx") }).then(f => console.log("wrote", f));
