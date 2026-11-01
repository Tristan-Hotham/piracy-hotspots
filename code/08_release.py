"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23856383, https://doi.org/10.5281/zenodo.23856383 and https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Pirate_Hotspots_Then_and_Now"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
I = R["imb"]
assert [I["y2023"], I["y2024"], I["y2025"], I["q3_2026"]] == [120, 116, 137, 51]
assert [I["sin_2024"], I["sin_2025"], I["sin_q3_2026"]] == [43, 80, 13]
assert [I["idn_2023"], I["idn_2024"], I["idn_2025"], I["idn_q3_2026"]] == [18, 22, 12, 6]
assert [I["gog_2023"], I["gog_2024"], I["gog_2025"], I["gog_q3_2026"]] == [22, 18, 21, 2]
assert 115 <= min(I["y2021"], I["y2022"]) and max(I[k] for k in ("y2021", "y2022", "y2023", "y2024", "y2025")) == 137
E = R["eras"]
pb = [round(100 * e["by_type"][0] / e["n"]) for e in E]
assert pb == [67, 67, 66, 43, 72, 76], pb
assert round(100 * E[3]["by_type"][3] / E[3]["n"]) == 45 and round(100 * E[3]["by_type"][1] / E[3]["n"]) == 12 and round(100 * E[5]["by_type"][2] / E[5]["n"]) == 7
assert 180 <= R["som_km_peak"] <= 220 and R["som"]["max_km"] < 1100
K = [k[2] for k in R["km_by_year"] if k[0] >= 1995]
assert 3 <= min(K) and max(K) <= 13                                                               # "median line near 5 to 12 km" (roughly)
assert R["ship"]["top1_pct_attacks"] < 1
assert [round(b["attacks_pct"]) for b in R["ship"]["bins"][1:]] == [22, 20, 36, 15, 6] and round(R["ship"]["bins"][0]["attacks_pct"], 1) == .5

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Pirate hotspots, then and now",
        "slug": "piracy-hotspots",
        "excerpt": f"I mapped {R['n']:,} pirate attacks from 1993 to 2020 and followed the hotspots as they moved, from the Strait of Malacca to Somalia and the Gulf of Guinea. In 2025 the busiest pirate waters were the Singapore Strait, and in 2026 Somali hijackers are back.",
        "seo_description": f"{R['n']:,} pirate attacks mapped, 1993 to 2020, with IMB counts to 2026: how piracy moved from Malacca to Somalia, West Africa and Singapore.",
        "tags": ["piracy", "maps", "data visualisation", "maritime history", "Somalia", "Gulf of Guinea", "Strait of Malacca", "Singapore Strait", "open data"],
        "header_alt": f"Title card reading 'Pirate hotspots, then and now' in black and red on pale paper, above three small world maps for 1993 to 1999, 2008 to 2011 and 2016 to 2020 with attacks shown as orange and red hexagons: clustered in Southeast Asia, then around Somalia and the Gulf of Aden, then off West Africa. Text: {R['n']:,} attacks mapped; Somali waters peaked at {R['som']['peak_n']} attacks in {R['som']['peak_year']}; the Singapore Strait had {I['sin_2025']} incidents in 2025."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/piracy-hotspots_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"piracy-hotspots/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"piracy-hotspots/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "piracy-hotspots/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "Pirate Hotspots, Then and Now: How Maritime Piracy Moved around the World, 1993 to 2026",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/}}.</p><p>Data: Benden, Feng, Howell and Dalla Riva (2021), Crime at Sea: A Global Database of Maritime Pirate Attacks (1993 to 2020), Journal of Open Humanities Data, CC BY 4.0; ICC International Maritime Bureau headline counts, 2021 to 2026; World Bank and IMF Global Shipping Traffic Density, CC BY 4.0; Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["maritime piracy", "armed robbery at sea", "Somalia", "Gulf of Guinea", "Strait of Malacca", "Singapore Strait", "IMB", "shipping", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5334/johd.39", "relation": "isDerivedFrom", "resource_type": "publication-article"},
                                 {"identifier": "https://github.com/newzealandpaul/Maritime-Pirate-Attacks", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://datacatalog.worldbank.org/search/dataset/0037580", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

# Reddit post text
S, G = R["som"], R["gog"]
post_md = f"""## Title

[OC] Where the pirates went: {R['n']:,} pirate attacks on ships mapped from 1993 to 2020, from the Strait of Malacca to Somalia ({S['peak_n']} attacks in {S['peak_year']}) to the Gulf of Guinea, and where piracy is today

## Body

I mapped every attack in the open Crime at Sea database ({R['n']:,} attacks and attempts, 1993 to 2020, built from International Maritime Bureau and US NGA reports) and grouped them into six eras. The hotspots keep moving. In the 1990s the South China Sea and Indonesia led; the Strait of Malacca peaked at {R['mal']['peak_n']} attacks in {R['mal']['peak_year']} and then fell away. In 2008 to 2011 Somali waters had {S['pct_world_08_11']:.0f}% of all attacks, often far out at sea (median {round(S['median_km_08_11'])} km from shore, against {R['not_som_km_08_11']:.0f} km elsewhere), then collapsed by {S['drop_pc_11_13']:.0f}% in two years. By 2020 the Gulf of Guinea had {G['pct_2020']:.0f}% of the world's attacks. The database stops in 2020, so the bottom panels use the IMB's headline counts: in 2025 the Singapore Strait had {I['sin_2025']} of the world's {I['y2025']} incidents, and all {I['hij_q3_2026']} hijackings in January to September 2026 were by Somali pirates. Caveat: these are reported attacks, and many attacks on small boats are never reported. Interactive map with a year slider: https://maps.tristanhotham.com/piracy-hotspots/

## Source comment

Sources: Benden, Feng, Howell and Dalla Riva (2021), Crime at Sea: A Global Database of Maritime Pirate Attacks (1993 to 2020), Journal of Open Humanities Data, https://doi.org/10.5334/johd.39 (CC BY 4.0; from IMB Piracy Reporting Centre reports and NGA ASAM); ICC International Maritime Bureau annual reports and press releases, 2021 to 2026 (headline counts); World Bank and IMF Global Shipping Traffic Density, AIS 2015 to 2021 (CC BY 4.0); Natural Earth outlines (public domain).

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/piracy-hotspots/
Paper: {{https://doi.org/10.5281/zenodo.23856383}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/}}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in post_md, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post_md)
print("reddit title chars", len(post_md.splitlines()[2]))
