"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Pirate_Hotspots_Then_and_Now"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
Y = {r[0]: r[1:] for r in R["years"]}
assert Y[1997][R_SCS] > Y[1997][R_IDN] and Y[1998][R_IDN] > Y[1998][R_SCS]                         # Indonesia overtook in 1998
assert max(R["by_year"][str(y)] for y in range(2000, 2012)) == R["peak_n"]
assert R["eras"][4]["top_region"] == R_SIN
assert R["cell_rank"][0] == "Chittagong anchorages, Bangladesh"
assert {"Jakarta and Tanjung Priok, Indonesia", "Chittagong anchorages, Bangladesh", "Belawan, Sumatra, Indonesia"} == {h["name"] for h in R["eras"][0]["hotspots"][:3]}
assert R["som"]["hij_2012"] > R["imb"]["hij_q3_2026"] and all(Y[y][R_SOM] < 20 for y in range(2015, 2021))


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}".replace("-", "$-$")
    return tex(str(v))


rows = "".join(f"{tex(r['name'])} & {r['n']:,} & {r['pct']:.1f}\\% & {r['peak_year']} ({r['peak_n']}) & {r['median_km']:.1f} & {r['hij_pct']:.0f}\\%\\\\\n" for r in R["regions"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Attacks by region, 1993 to 2020: total, share, peak year (attacks), median distance from shore and share hijacked.}\\label{tab:regions}"
      "\\begin{tabular}{p{6.2cm}rrrrr}\\toprule Region & Attacks & Share & Peak year & Median km & Hijacked\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for e in R["eras"]:
    for k, h in enumerate(e["hotspots"][:5]):
        rows += (f"{tex(e['name']) if k == 0 else ''} & {tex(h['name'])} & {h['n']:,} & {h['pct']:.1f}\\%\\\\\n")
    rows += "\\addlinespace\n"
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{The five busiest 1 degree squares in each era, with their share of the era's attacks.}\\label{tab:hotspots}"
      "\\begin{tabular}{llrr}\\toprule Era & Square & Attacks & Share\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
I = R["imb"]
val = {"2021": I["y2021"], "2022": I["y2022"], "2023": I["y2023"], "2024": I["y2024"], "2025": I["y2025"], "2025 Jan-Sep": I["q3_2025"], "2026 Jan-Sep": I["q3_2026"]}
sin = {"2024": I["sin_2024"], "2025": I["sin_2025"], "2025 Jan-Sep": I["sin_q3_2025"], "2026 Jan-Sep": I["sin_q3_2026"]}
idn = {"2023": I["idn_2023"], "2024": I["idn_2024"], "2025": I["idn_2025"], "2025 Jan-Sep": 9, "2026 Jan-Sep": I["idn_q3_2026"]}
gog = {"2023": I["gog_2023"], "2024": I["gog_2024"], "2025": I["gog_2025"], "2026 Jan-Sep": I["gog_q3_2026"]}
import pandas as pd
IM = pd.read_csv(f"{DATA}/imb_recent.csv")
assert int(IM.loc[IM.period == "2025 Jan-Sep", "indonesia"].iloc[0]) == idn["2025 Jan-Sep"]
g = lambda d, p: f"{d[p]}" if p in d and d[p] is not None else ""
rows = "".join(f"{p.replace('Jan-Sep', 'Jan to Sep')} & {val[p]} & {g(sin, p)} & {g(idn, p)} & {g(gog, p)}\\\\\n" for p in IM.period)
TI = ("\\begin{table}[tbp]\\centering\\small\\caption{IMB headline incident counts, 2021 to January to September 2026, transcribed from IMB annual reports and press releases (blank where not given). Sources are listed with the data (data/imb\\_recent.csv).}\\label{tab:imb}"
      "\\begin{tabular}{lrrrr}\\toprule Period & World & Singapore Strait & Indonesia & Gulf of Guinea\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("{{meta.doi}}", "@@DOI@@")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("REGIONS", TR), ("HOTSPOTS", TH), ("IMB", TI)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
