"""Build slides.html (printed to PDF) from content.json."""
import json
from html import escape as E
from pathlib import Path

HERE = Path(__file__).parent
C = json.loads((HERE / "content.json").read_text())
li = lambda items: "".join(f"<li>{E(t)}</li>" for t in items)
rows = lambda head, body: "<tr>" + "".join(f"<th>{E(h)}</th>" for h in head) + "</tr>" + "".join(
    "<tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in body)

segs = "".join(f"""<div class="seg"><h2>{E(h)} <span class="n">({E(sub)})</span> <i class="n">{E(q)}</i></h2>
  <ul>{li(items)}</ul></div>""" for h, sub, q, items in C["segs"])
proof = "".join(f"<li><b>{E(a)}</b>{E(b)}</li>" for a, b in C["proof"])

html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Group 7 model slides</title>
<style>
@page {{ size: 13.333in 7.5in; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #000; background: #fff; }}
.slide {{ width: 13.333in; height: 7.5in; padding: 0.45in 0.7in; page-break-after: always; overflow: hidden; position: relative; }}
h1 {{ font-size: 23pt; margin: 0 0 0.18in; line-height: 1.15; }}
h2 {{ font-size: 13pt; margin: 0 0 3pt; }}
p, li, td, th {{ font-size: 11pt; line-height: 1.28; margin: 0 0 3pt; }}
ul, ol {{ margin: 0; padding-left: 15pt; }}
.cols {{ display: flex; gap: 0.35in; }}
.col {{ flex: 1; }}
.seg {{ border: 1px solid #000; padding: 5pt 9pt; }}
.n {{ font-weight: normal; }}
.small, .small li {{ font-size: 9.5pt; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #000; padding: 3pt 5pt; text-align: left; vertical-align: top; }}
.title {{ display: flex; flex-direction: column; justify-content: center; }}
.title h1 {{ font-size: 30pt; }}
.title p {{ font-size: 16pt; margin: 4pt 0; }}
</style></head><body>

<section class="slide title">
  <h1>{E(C["title"])}</h1>
  {"".join(f"<p>{E(t)}</p>" for t in C["title_lines"])}
</section>

<section class="slide">
  <h1>{E(C["s2_title"])}</h1>
  <div class="cols" style="gap:0.4in">
    <div class="col" style="display:flex;flex-direction:column;gap:7pt">{segs}</div>
    <div class="col">
      <h2>{E(C["proof_title"])}</h2>
      <img src="../outputs/elbow.png" alt="Chart: how much hires differ from their group, by number of groups" style="width:80%">
      <ul class="small">{proof}</ul>
    </div>
  </div>
</section>

<section class="slide">
  <h1>{E(C["s3_title"])}</h1>
  <div class="cols">
    <div class="col" style="flex:0.85">
      <h2>{E(C["how_title"])}</h2><ol>{li(C["how"])}</ol>
      <h2 style="margin-top:8pt">{E(C["example_title"])}</h2><p>{E(C["example"])}</p>
      <h2 style="margin-top:8pt">{E(C["ease_title"])}</h2><p>{E(C["ease"])}</p>
    </div>
    <div class="col" style="flex:1.5">
      <table>{rows(C["pages_head"], C["pages"])}</table>
      <h2 style="margin-top:12pt">{E(C["value_title"])}</h2>
      <p>{E(C["value_text"])}</p>
      <table>{rows(C["value_head"], C["value_rows"])}</table>
    </div>
  </div>
  <p class="small" style="position:absolute;left:0.7in;right:0.7in;bottom:0.35in">{E(C["foot"])}</p>
</section>
</body></html>
"""
(HERE / "slides.html").write_text(html)
print("wrote slides.html")
