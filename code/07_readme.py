"""README.md and LICENSE, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
I = R["imb"]; S = R["som"]; G = R["gog"]; M = R["mal"]
f = lambda v: f"{round(v):,}"
readme = f"""# Pirate hotspots, then and now

Where pirates attack ships, and how the hotspots moved: {R['n']:,} attacks and attempted attacks from 1993 to 2020 mapped year by year from the Crime at Sea database (Benden, Feng, Howell and Dalla Riva, 2021, built from IMB and NGA ASAM reports), with the International Maritime Bureau's headline counts for 2021 to September 2026 to bring the story up to today, and the World Bank and IMF map of ship traffic.

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: https://doi.org/{{10.5281/zenodo.23856383}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/}}

## Headline results

- The hotspots moved. 1993 to 1999: the South China Sea, Philippines and East Asia led ({R['scs']['pct_93_99']:.0f}% of attacks), with Indonesia overtaking them by 1998 and peaking at {R['idn']['peak_n']} attacks in {R['idn']['peak_year']}. The Strait of Malacca peaked at {M['peak_n']} in {M['peak_year']}, then fell to {M['n_2005']} in 2005 and about {f(M['avg_06_20'])} a year after.
- Somalia: attacks in Somali waters, the Gulf of Aden, the southern Red Sea and the Arabian Sea rose from {S['n_2007']} in 2007 to {S['peak_n']} in {S['peak_year']}: {S['pct_world_08_11']:.0f}% of all attacks and {S['hij_08_11']} of the {S['hij_world_08_11']} hijackings in 2008 to 2011. Then they fell {S['drop_pc_11_13']:.0f}% in two years; only {S['hij_14_20']} hijackings there from 2014 to 2020.
- Far out at sea: half of all attacks were within {R['km_median']:.1f} km of shore, but Somali attacks had a median distance of {f(S['median_km_08_11'])} km in 2008 to 2011 ({f(R['som_km_peak'])} km in {R['som_km_peak_year']}).
- The Gulf of Guinea led by 2016 to 2020: {G['peak_n']} attacks in {G['peak_year']} and {G['pct_2020']:.0f}% of the world's in 2020.
- Today (IMB headline counts): {I['y2025']} incidents worldwide in 2025, {I['sin_2025']} of them ({I['sin_pct_2025']:.0f}%) in the Singapore Strait, about as many as its 2015 peak of {R['sin']['peak_n']}. In January to September 2026: {I['q3_2026']} incidents ({I['q3_drop_pc']:.0f}% fewer than a year earlier), and all {I['hij_q3_2026']} hijackings were by Somali pirates.
- Most piracy is theft: {R['types'][0]['pct']:.0f}% of attacks were boardings and {R['types'][1]['pct']:.0f}% hijackings. {R['ship']['top25_pct_attacks']:.0f}% of attacks were in the busiest quarter of 1 degree squares by ship traffic, but the very busiest 1% (around Europe) had only {R['ship']['top1_pct_attacks']:.1f}%.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; results, world outline and city names embedded; `data/points.json`, `data/details.json` and `data/shipping.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/attacks.csv` | All {R['n']:,} attacks with date, position, attack type (merged) and type as recorded, vessel status, type and name, region, era, nearest and EEZ country, distance from shore, location and IMB description (2015 to 2020), and source. CC BY 4.0, from Benden et al. (2021). |
| `data/attacks_by_year_region.csv` | Attacks per year and region, 1993 to 2020. |
| `data/hotspots_by_era.csv` | The eight busiest 1 degree squares in each era. |
| `data/imb_recent.csv` | IMB headline counts, 2021 to January to September 2026, with the source of each row. |
| `data/shipping_1deg.csv` | World Bank and IMF AIS ship density (2015 to 2021) averaged over 1 degree squares from the subsampled overview raster. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/details.json`, `data/shipping.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data: attack points, record details, shipping classes, labels, Natural Earth outlines and city names. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates; `qa.js` takes screenshots with Playwright. |
| `release/` | Paper PDF and LaTeX source with figures, blog post, figures and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, `pirate_hotspots.png`) and post text. |

## Method in brief

- Attacks: the Crime at Sea database as published on GitHub. "Boarded" and "Boarding" (used in alternate years for the same thing) merged; "Fired upon" is coded almost only from 2015, when the source switches from the MAPPING piracy data ({R['src_mapping']:,} attacks, 1993 to 2014) to IMB reports ({R['src_imb']:,}, 2015 to 2020).
- Regions, by the first rule that applies: Singapore Strait (box 103.42 to 104.65 E, 0.85 to 1.60 N); Strait of Malacca (polygon); Indonesian waters; South China Sea, Philippines and East Asia; Indian subcontinent (within 300 km); East African coast (within 60 km, Kenya to South Africa); Somali waters (32 to 80 E, 15 S to 30 N, outside the Persian Gulf); Gulf of Guinea and West Africa; Americas; elsewhere (see `code/common.py`).
- Eras: 1993 to 1999, 2000 to 2004, 2005 to 2007, 2008 to 2011, 2012 to 2015, 2016 to 2020. Hotspots: 1 degree squares, named from the attacks' location descriptions.
- Shipping: the 0.08 degree overview of the World Bank and IMF density raster is a subsample, so it is only used averaged to 1 degree squares; squares ranked by traffic.
- Today: IMB headline counts transcribed from its annual reports and press releases, kept apart from the mapped data.
- Caveats: reported attacks only, with heavy under-reporting of attacks on small and local craft; a coding change at 2015; some anchorage positions copied from earlier incidents; the shipping map covers 2015 to 2021 and favours areas with dense coastal AIS reception; country indicators show correlation, not cause.

## How to rerun

Needs Python 3 with pandas, numpy, scipy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex and pdftotext; Node with Playwright for QA. Raw inputs are read in place from `/home/claude/newdata/raw6/` (`piracy/` and `shipdensity/`) and `/home/claude/newdata/raw/geo/` (set in `code/common.py`). Intermediate files go to `/dev/shm/piracy/work` (set `PIRTMP` to change).

```
cd code
python3 02_geo.py          # world outline, country and city names
python3 01_clean.py        # attacks, regions, IMB counts, shipping squares
python3 03_results.py      # results.json and page data
python3 04_build_site.py   # index.html
python3 05_figures.py      # header, blog and paper figures
python3 06_paper.py        # paper PDF
python3 07_readme.py       # README and LICENSE
python3 08_release.py      # blog post, Zenodo files
python3 ../reddit/collage.py
```

## Sources and licences

- Benden, P., Feng, A., Howell, C. and Dalla Riva, G. V. (2021) Crime at Sea: A Global Database of Maritime Pirate Attacks (1993 to 2020). Journal of Open Humanities Data 7: 19. https://doi.org/10.5334/johd.39. Data: https://github.com/newzealandpaul/Maritime-Pirate-Attacks, CC BY 4.0 (from IMB Piracy Reporting Centre reports and NGA Anti-Shipping Activity Messages, with the MAPPING piracy data of Brandon Prins).
- ICC International Maritime Bureau, Piracy and Armed Robbery Against Ships reports and press releases, 2021 to 2026: headline counts only, with sources in `data/imb_recent.csv`.
- World Bank and IMF, Global Shipping Traffic Density (AIS, 2015 to 2021), CC BY 4.0. https://datacatalog.worldbank.org/search/dataset/0037580
- Natural Earth countries and populated places (public domain). Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Pirate hotspots, then and now: how maritime piracy moved around the world, 1993 to 2026. Zenodo. https://doi.org/{{10.5281/zenodo.23856383}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of the code in this repository (the code/
and reddit/ folders), to deal in the code without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the code, and to permit persons to whom the code is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the code.

THE CODE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE CODE OR THE USE OR OTHER DEALINGS IN THE CODE.

Text, figures and derived data

The text, figures, page and derived data are licensed under the Creative Commons Attribution 4.0 International licence
(CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). The attack data are derived from Benden, Feng, Howell and
Dalla Riva (2021), Crime at Sea, CC BY 4.0; the shipping density data from the World Bank and IMF, CC BY 4.0. Please credit
those sources as well as this work.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
