"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json, details.json and
shipping.json are loaded by the page. Facts stated in words (page, blog, paper, collage) are checked here.
10.5281/zenodo.23856383 and https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/ stay as placeholders for the publisher."""
import json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")

# facts stated in words
assert min(R["by_year"][str(y)] for y in (2009, 2010, 2011)) > 400
Y = {r[0]: r[1:] for r in R["years"]}
assert Y[1999][R_IDN] > Y[1999][R_SCS] and Y[1995][R_SCS] > Y[1995][R_IDN] and Y[1998][R_IDN] > Y[1998][R_SCS]   # Indonesia overtakes as the 1990s end
E = R["eras"]
assert RSHORT[E[0]["top_region"]] == "South China Sea" and RSHORT[E[3]["top_region"]] == "Somali waters" and RSHORT[E[5]["top_region"]] == "Gulf of Guinea"
assert sum("Gulf of Aden" in h["name"] for h in E[3]["hotspots"][:5]) == 2                                   # "only two Gulf of Aden squares reach the top five"
assert {"Hong Kong waters", "Bangkok Bar and Laem Chabang, Thailand"} <= {h["name"] for h in E[0]["hotspots"]}
D = pd.read_csv(f"{DATA}/attacks.csv", keep_default_na=False)
s = D[(D.region == REGIONS[R_SCS][0]) & (D.year <= 1999)].nearest_country.value_counts()
assert list(s.index[:2]) == ["CHN", "PHL"]                                                                    # Hong Kong ... around the Philippines
assert R["imb"]["y2022"] == min(R["imb"][k] for k in ("y2021", "y2022", "y2023", "y2024", "y2025"))
assert R["imb"]["y2025"] == max(R["imb"][k] for k in ("y2021", "y2022", "y2023", "y2024", "y2025"))
assert R["som"]["n_08_11"] == sum(Y[y][R_SOM] for y in range(2008, 2012))
assert R["som"]["peak_n"] == Y[2011][R_SOM] and R["som"]["n_2013"] < 20
assert R["gog"]["pct_2020"] > 40 and R["mal"]["n_2005"] < R["mal"]["avg_00_04"] / 2
assert R["ship"]["top1_pct_attacks"] < 1
assert R["som_km_peak_year"] == 2010 and R["som"]["median_km_08_11"] > 100
assert abs(R["imb"]["sin_2025"] - R["sin"]["peak_n"]) <= 1                                                     # "about as many as the 2015 peak"
assert R["imb"]["sin_q3_2026"] < R["imb"]["sin_q3_2025"] / 4                                                 # "the Singapore Strait went quiet"


def fill(tpl):
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = [x for x in re.findall(r"\{\{[^}]*\}\}", html) if x not in ("10.5281/zenodo.23856383", "https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/")]
    assert not left, left[:5]
    return html


def build():
    html = fill(open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read())
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
