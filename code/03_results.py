"""Every number quoted anywhere (page, paper, blog, collage, post) goes into data/results.json. Also writes the page data
(data/site.json, data/points.json, data/details.json, data/shipping.json) and tidy tables (data/*.csv)."""
import math
import numpy as np
import pandas as pd
from common import *

D = pd.read_csv(f"{DATA}/attacks.csv", keep_default_na=False, na_values=[""])
for c in ("vessel_name", "location", "description", "vessel_type", "nearest_country", "eez_country", "eez_country_name", "nearest_country_name"):
    D[c] = D[c].fillna("")
RI = {r[0]: i for i, r in enumerate(REGIONS)}
TI = {t[0]: i for i, t in enumerate(TYPES)}
EI = {e[0]: i for i, e in enumerate(ERAS)}
D["r"] = D.region.map(RI); D["t"] = D.attack_type.map(TI); D["e"] = D.era.map(EI)
D["s"] = D.vessel_status.map(lambda s: STATUS.index(s) if s in STATUS[:3] else (4 if s == "Not recorded" else 3))
D["cy"] = np.floor(D.lat).astype(int); D["cx"] = np.floor(D.lon).astype(int)
YEARS = list(range(1993, 2021))
N = len(D)
pc = lambda a, b: 100.0 * a / b
R = {"meta": {"page": PAGE, "repo": REPO, "slug": SLUG, "doi": DOI, "retrieved": "2026"}}

# ---------- totals and years ----------
by_year = D.groupby("year").size().reindex(YEARS, fill_value=0)
YR = pd.crosstab(D.year, D.r).reindex(index=YEARS, columns=range(len(REGIONS)), fill_value=0)
R["n"] = N
R["y0"], R["y1"] = 1993, 2020
R["peak_year"] = int(by_year.idxmax()); R["peak_n"] = int(by_year.max())
R["low_year"] = int(by_year.idxmin()); R["low_n"] = int(by_year.min())
R["n_2020"] = int(by_year[2020])
R["years"] = [[y] + [int(v) for v in YR.loc[y]] for y in YEARS]
R["by_year"] = {str(y): int(by_year[y]) for y in YEARS}
R["src_mapping"] = int((D.year <= 2014).sum()); R["src_imb"] = int((D.year >= 2015).sum())
R["n_2009_11"] = int(by_year.loc[2009:2011].sum())
R["min_00_11"] = int(by_year.loc[2000:2011].min())

# ---------- regions ----------
regs = []
for i, (name, col) in enumerate(REGIONS):
    s = D[D.r == i]; yy = YR[i]
    regs.append({"name": name, "short": RSHORT[i], "n": int(len(s)), "pct": pc(len(s), N), "peak_year": int(yy.idxmax()),
                 "peak_n": int(yy.max()), "median_km": float(s.shore_km.median()),
                 "hijacked": int((s.t == 1).sum()), "hij_pct": pc((s.t == 1).sum(), len(s)),
                 "anchored_pct": pc((s.s == 0).sum(), len(s)), "steaming_pct": pc((s.s == 2).sum(), len(s))})
R["regions"] = regs

# ---------- eras: leading region and hotspot cells ----------
eras = []
for k, (name, a, b) in enumerate(ERAS):
    s = D[D.e == k]; rc = s.groupby("r").size().sort_values(ascending=False)
    cells = s.groupby(["cy", "cx"]).size().sort_values(ascending=False).head(8)
    hs = []
    for (cy, cx), n in cells.items():
        cs = s[(s.cy == cy) & (s.cx == cx)]
        assert (cy, cx) in CELLNAME, (name, cy, cx)
        hs.append({"name": CELLNAME[(cy, cx)], "lat": cy, "lon": cx, "n": int(n), "pct": pc(n, len(s)),
                   "region": int(cs.r.mode()[0]), "country": cs.nearest_country_name.mode()[0].replace(", Rep.", "").replace(", RB", "")})
    eras.append({"name": name, "a": a, "b": b, "n": int(len(s)), "per_year": len(s) / (b - a + 1), "top_region": int(rc.index[0]),
                 "top_region_n": int(rc.iloc[0]), "top_region_pct": pc(rc.iloc[0], len(s)),
                 "by_region": [int((s.r == i).sum()) for i in range(len(REGIONS))],
                 "by_type": [int((s.t == i).sum()) for i in range(len(TYPES))],
                 "top10_cells_pct": pc(s.groupby(["cy", "cx"]).size().sort_values(ascending=False).head(10).sum(), len(s)),
                 "hotspots": hs})
R["eras"] = eras
assert [RSHORT[e["top_region"]] for e in eras] == ["South China Sea", "Indonesia", "Indonesia", "Somali waters", "Singapore Strait", "Gulf of Guinea"], [RSHORT[e["top_region"]] for e in eras]
R["cells_all"] = int(D.groupby(["cy", "cx"]).ngroups)
top_all = D.groupby(["cy", "cx"]).size().sort_values(ascending=False)
R["top_cell_all"] = {"name": CELLNAME[top_all.index[0]], "n": int(top_all.iloc[0])}
R["top20_cells_pct"] = pc(top_all.head(20).sum(), N)

# ---------- the story, region by region ----------
y = lambda i, a, b=None: int(YR[i].loc[a:(b or a)].sum())
R["scs"] = {"n_93_99": y(R_SCS, 1993, 1999), "pct_93_99": pc(y(R_SCS, 1993, 1999), eras[0]["n"]), "n_1995": y(R_SCS, 1995),
            "n_16_20": y(R_SCS, 2016, 2020)}
R["sea93"] = {"n_93_04": int(D[(D.year <= 2004) & D.r.isin([R_SCS, R_IDN, R_MAL, R_SIN])].shape[0])}
R["sea93"]["pct_93_04"] = pc(R["sea93"]["n_93_04"], int((D.year <= 2004).sum()))
R["idn"] = {"n": regs[R_IDN]["n"], "peak_year": regs[R_IDN]["peak_year"], "peak_n": regs[R_IDN]["peak_n"],
            "n_99_04": y(R_IDN, 1999, 2004), "n_16_20": y(R_IDN, 2016, 2020)}
mal = YR[R_MAL]
R["mal"] = {"n": regs[R_MAL]["n"], "peak_year": int(mal.idxmax()), "peak_n": int(mal.max()), "avg_00_04": mal.loc[2000:2004].mean(),
            "avg_06_20": mal.loc[2006:2020].mean(), "max_06_20": int(mal.loc[2006:2020].max()), "n_2004": int(mal[2004]), "n_2005": int(mal[2005])}
R["mal"]["fall_x"] = R["mal"]["avg_00_04"] / R["mal"]["avg_06_20"]
assert R["mal"]["peak_year"] == 2000 and R["mal"]["max_06_20"] < R["mal"]["avg_00_04"] / 1.5
som = YR[R_SOM]; S = D[D.r == R_SOM]
S8 = S[S.year.between(2008, 2011)]
R["som"] = {"n": regs[R_SOM]["n"], "n_08_11": int(len(S8)), "pct_world_08_11": pc(len(S8), eras[3]["n"]), "peak_year": int(som.idxmax()),
            "peak_n": int(som.max()), "n_2007": int(som[2007]), "n_2012": int(som[2012]), "n_2013": int(som[2013]), "n_2014": int(som[2014]),
            "n_15_20": int(som.loc[2015:2020].sum()), "hij_08_11": int((S8.t == 1).sum()),
            "hij_world_08_11": int(((D.t == 1) & D.year.between(2008, 2011)).sum()),
            "att_pct_08_11": pc((S8.t == 3).sum(), len(S8)), "steam_pct_08_11": pc((S8.s == 2).sum(), len(S8)),
            "median_km_08_11": float(S8.shore_km.median()), "far_pct_08_11": pc((S8.shore_km > 185.2).sum(), len(S8)),
            "max_km": float(S.shore_km.max()), "n_over_1000": int((S.shore_km > 1000).sum()),
            "hij_12_20": int(((S.t == 1) & (S.year >= 2012)).sum())}
R["som"]["hij_pct_world_08_11"] = pc(R["som"]["hij_08_11"], R["som"]["hij_world_08_11"])
R["som"]["drop_pc_11_13"] = pc(som[2011] - som[2013], som[2011])
gog = YR[R_GOG]
R["gog"] = {"n": regs[R_GOG]["n"], "peak_year": int(gog.idxmax()), "peak_n": int(gog.max()), "n_2020": int(gog[2020]), "n_2019": int(gog[2019]),
            "n_16_20": int(gog.loc[2016:2020].sum()), "pct_16_20": pc(gog.loc[2016:2020].sum(), eras[5]["n"]),
            "pct_2020": pc(gog[2020], by_year[2020]), "pct_93_99": pc(gog.loc[1993:1999].sum(), eras[0]["n"]),
            "fired_16_20": int(((D.r == R_GOG) & (D.t == 2) & (D.year >= 2016)).sum()),
            "fired_world_16_20": int(((D.t == 2) & (D.year >= 2016)).sum()),
            "kmed_93_15": float(D[(D.r == R_GOG) & (D.year <= 2015)].shore_km.median()),
            "kmed_16_20": float(D[(D.r == R_GOG) & (D.year >= 2016)].shore_km.median()),
            "far_16_20": int(((D.r == R_GOG) & (D.year >= 2016) & (D.shore_km > 92.6)).sum())}
assert R["gog"]["peak_year"] == 2018 and R["gog"]["n_2020"] >= R["gog"]["peak_n"] - 2
G5 = D[(D.r == R_GOG) & (D.year >= 2016)]
R["gog"]["kidnap_desc_16_20"] = int(G5.description.str.contains("kidnap", case=False).sum())
sin = YR[R_SIN]
R["sin"] = {"n": regs[R_SIN]["n"], "peak_year": int(sin.idxmax()), "peak_n": int(sin.max()), "n_2013": int(sin[2013]), "n_2016": int(sin[2016]),
            "avg_93_08": sin.loc[1993:2008].mean(), "n_12_15": int(sin.loc[2012:2015].sum()), "n_2020": int(sin[2020])}
S5 = D[(D.r == R_SIN) & D.year.between(2014, 2015)]
R["sin"]["boarded_pct_14_15"] = pc((S5.t == 0).sum(), len(S5)); R["sin"]["n_14_15"] = int(len(S5))
assert R["sin"]["peak_year"] == 2015
cellrank = [CELLNAME[k] for k in top_all.index[:5]]
R["cell_rank"] = cellrank
assert cellrank.index("Lagos anchorages, Nigeria") == 3
ind = YR[R_IND]
R["ind"] = {"n": regs[R_IND]["n"], "peak_year": int(ind.idxmax()), "peak_n": int(ind.max()),
            "chitt": int(top_all.get((22, 91), 0))}
R["ame"] = {"n": regs[R_AME]["n"], "n_16_20": y(R_AME, 2016, 2020), "ven_16_20": int(((D.year >= 2016) & (D.nearest_country == "VEN")).sum())}

# ---------- attack types ----------
tt = D.groupby("t").size().reindex(range(len(TYPES)), fill_value=0)
R["types"] = [{"name": TYPES[i][0], "n": int(tt[i]), "pct": pc(tt[i], N)} for i in range(len(TYPES))]
R["fired_before_2015"] = int(((D.t == 2) & (D.year < 2015)).sum()); R["fired_from_2015"] = int(((D.t == 2) & (D.year >= 2015)).sum())
R["n_1993_untyped"] = int(((D.year == 1993) & (D.t == 4)).sum())
R["boarded_pct_16_20"] = pc(eras[5]["by_type"][0], eras[5]["n"])
R["boarded_pct_08_11"] = pc(eras[3]["by_type"][0], eras[3]["n"])
R["hij_total"] = int(tt[1]); R["hij_peak_year"] = int(D[D.t == 1].groupby("year").size().idxmax()); R["hij_peak_n"] = int(D[D.t == 1].groupby("year").size().max())
R["hij_16_20"] = int(((D.t == 1) & (D.year >= 2016)).sum())

# ---------- vessel status and distance from shore ----------
R["status"] = [{"name": STATUS[i], "n": int((D.s == i).sum()), "pct": pc((D.s == i).sum(), N)} for i in range(len(STATUS))]
known = D[D.s.isin([0, 1, 2])]
R["anchored_berthed_pct_known"] = pc(known.s.isin([0, 1]).sum(), len(known))
R["km_median"] = float(D.shore_km.median())
R["km_anch_median"] = float(D[D.s == 0].shore_km.median())
R["km_steam_median"] = float(D[D.s == 2].shore_km.median())
R["within_20_pct"] = pc((D.shore_km <= 20).sum(), N)
R["far_pct"] = pc((D.shore_km > 185.2).sum(), N)
R["far_n"] = int((D.shore_km > 185.2).sum())
R["far_som_pct"] = pc(((D.shore_km > 185.2) & (D.r == R_SOM)).sum(), R["far_n"])
R["not_som_median_km"] = float(D[D.r != R_SOM].shore_km.median())
R["not_som_km_08_11"] = float(D[(D.r != R_SOM) & D.year.between(2008, 2011)].shore_km.median())
kmy = []
for yy in YEARS:
    s = D[D.year == yy]; a = s[s.r == R_SOM].shore_km; b = s[s.r != R_SOM].shore_km
    kmy.append([yy, round(float(a.median()), 1) if len(a) >= 5 else None, round(float(b.median()), 1), int(len(a))])
R["km_by_year"] = kmy
R["som_km_peak_year"] = max((k for k in kmy if k[1] is not None), key=lambda k: k[1])[0]
R["som_km_peak"] = max(k[1] for k in kmy if k[1] is not None)

# ---------- shipping lanes (World Bank AIS density, 1 degree) ----------
M = np.load(f"{WORK}/shipping_1deg.npy")
ok = np.isfinite(M) & (M > 0)
vals = np.sort(M[ok])
r_ = np.clip((89.5 - (D.cy + .5)).round().astype(int), 0, 179).values
c_ = np.clip((D.cx + 180).values, 0, 359)
av = np.nan_to_num(M[r_, c_])
pctile = np.searchsorted(vals, av, side="right") / len(vals) * 100
R["ship"] = {"cells": int(ok.sum()), "top10_pct_attacks": pc((pctile > 90).sum(), N), "top25_pct_attacks": pc((pctile > 75).sum(), N),
             "median_pctile": float(np.median(pctile)), "zero_pct": pc((av == 0).sum(), N),
             "top10_pct_som": pc(((pctile > 90) & (D.r == R_SOM).values).sum(), (D.r == R_SOM).sum()),
             "top10_pct_rest": pc(((pctile > 90) & (D.r != R_SOM).values).sum(), (D.r != R_SOM).sum())}
assert R["ship"]["top25_pct_attacks"] > 75
BINS = [("Busiest 1%", 99, 100.1), ("Next 4%", 95, 99), ("Next 5%", 90, 95), ("Next 15%", 75, 90), ("Next 25%", 50, 75), ("Quietest 50%", -1, 50)]
R["ship"]["bins"] = [{"name": n, "cells_pct": (min(b, 100) - max(a, 0)), "attacks_pct": pc(((pctile > a) & (pctile <= b)).sum(), N)} for n, a, b in BINS]
R["ship"]["top1_pct_attacks"] = R["ship"]["bins"][0]["attacks_pct"]
# page layer: 1 degree cells in 8 log classes
q = np.quantile(vals, [.5, .75, .9, .95, .98, .99, .995])
cells = []
for rr in range(180):
    for cc in range(360):
        if ok[rr, cc]:
            k = int(np.searchsorted(q, M[rr, cc]))
            if k >= 1:
                cells.append([int(89 - rr), int(cc - 180), k])
jsave({"note": "World Bank Global Shipping Traffic Density (AIS 2015 to 2021), summed to 1 degree cells; classes are quantiles of cells with traffic: 1 = top 50%, 2 = top 25%, 3 = top 10%, 4 = top 5%, 5 = top 2%, 6 = top 1%, 7 = top 0.5%", "cells": cells}, f"{DATA}/shipping.json")

# ---------- country indicators (correlation, not cause) ----------
CI = pd.read_csv(f"{RAW}/piracy/country_indicators.csv")
CI["cpi100"] = np.where(CI.year < 2012, CI.corruption_index * 10, CI.corruption_index)
E = D[(D.eez_country != "") & (D.year <= 2019)].groupby(["eez_country", "year"]).size().rename("n").reset_index()
J = E.merge(CI[["country", "year", "GDP", "cpi100"]], left_on=["eez_country", "year"], right_on=["country", "year"], how="left")
gmed = CI.groupby("year").GDP.median()
J["poor"] = J.GDP < J.year.map(gmed)
withg = J[J.GDP.notna()]
R["ind_ctx"] = {"eez_attacks": int(J.n.sum()), "with_gdp": int(withg.n.sum()), "below_median_gdp_pct": pc(withg[withg.poor].n.sum(), withg.n.sum()),
                "cpi_known": int(J[J.cpi100.notna()].n.sum()), "cpi_below35_pct": pc(J[J.cpi100 < 35].n.sum(), J[J.cpi100.notna()].n.sum()),
                "attacks_outside_eez_pct": pc((D.eez_country == "").sum(), N)}
ctry = J.groupby("eez_country").agg(n=("n", "sum"), gdp=("GDP", "median"), cpi=("cpi100", "median")).reset_index()
ctry = ctry[ctry.gdp.notna()]
from scipy.stats import spearmanr
rho = spearmanr(ctry.n, ctry.gdp)
R["ind_ctx"]["n_countries"] = int(len(ctry)); R["ind_ctx"]["rho_gdp"] = float(rho.statistic)
ctry.to_csv(f"{WORK}/ctry_ind.csv", index=False)

# ---------- IMB headline counts, 2021 to 2026 ----------
I = pd.read_csv(f"{DATA}/imb_recent.csv")
iv = lambda p, c: (None if pd.isna(I.loc[I.period == p, c].iloc[0]) else int(I.loc[I.period == p, c].iloc[0]))
R["imb"] = {"y2021": iv("2021", "total_incidents"), "y2022": iv("2022", "total_incidents"), "y2023": iv("2023", "total_incidents"),
            "y2024": iv("2024", "total_incidents"), "y2025": iv("2025", "total_incidents"), "q3_2025": iv("2025 Jan-Sep", "total_incidents"),
            "q3_2026": iv("2026 Jan-Sep", "total_incidents"),
            "sin_2024": iv("2024", "singapore_straits"), "sin_2025": iv("2025", "singapore_straits"), "sin_q3_2025": iv("2025 Jan-Sep", "singapore_straits"),
            "sin_q3_2026": iv("2026 Jan-Sep", "singapore_straits"),
            "idn_2023": iv("2023", "indonesia"), "idn_2024": iv("2024", "indonesia"), "idn_2025": iv("2025", "indonesia"), "idn_q3_2026": iv("2026 Jan-Sep", "indonesia"),
            "gog_2023": iv("2023", "gulf_of_guinea"), "gog_2024": iv("2024", "gulf_of_guinea"), "gog_2025": iv("2025", "gulf_of_guinea"), "gog_q3_2026": iv("2026 Jan-Sep", "gulf_of_guinea"),
            "hij_2025": iv("2025", "hijacked"), "hij_q3_2026": iv("2026 Jan-Sep", "hijacked"),
            "hostage_2025": iv("2025", "crew_hostage"), "kidnap_2025": iv("2025", "crew_kidnapped"), "kidnap_2024": iv("2024", "crew_kidnapped"),
            "phl_q3_2026": 9, "som_hostage_pct_2026": 94, "crew_q3_2026": 105, "hij_som_q3_2026": 8}
note26 = I.loc[I.period == "2026 Jan-Sep", "source"].iloc[0]
assert "8 hijackings all Somali" in note26 and "94%" in note26 and "Philippines 9" in note26 and "crew affected 105" in note26
im = R["imb"]
im["sin_pct_2025"] = pc(im["sin_2025"], im["y2025"])
im["sin_x_2025"] = im["sin_2025"] / im["sin_2024"]
im["q3_drop_pc"] = pc(im["q3_2025"] - im["q3_2026"], im["q3_2025"])
im["avg_21_25"] = (im["y2021"] + im["y2022"] + im["y2023"] + im["y2024"] + im["y2025"]) / 5
im["low_vs_peak_pc"] = pc(R["peak_n"] - im["y2022"], R["peak_n"])
im["sin_2025_vs_2015"] = im["sin_2025"] - R["sin"]["peak_n"]
im["sources"] = [{"period": p, "src": s} for p, s in zip(I.period, I.source)]
assert im["sin_2025"] >= R["sin"]["peak_n"] - 1 and im["y2025"] == max(im[k] for k in ("y2021", "y2022", "y2023", "y2024", "y2025"))
H = D[(D.r == R_SOM) & (D.t == 1)].groupby("year").size()
R["som"]["hij_14_20"] = int(H.loc[2014:2020].sum()); R["som"]["hij_2012"] = int(H.get(2012, 0)); R["som"]["hij_2017"] = int(H.get(2017, 0))
assert R["som"]["hij_14_20"] == R["som"]["hij_2017"] == 3

# ---------- tidy tables ----------
pd.DataFrame(R["years"], columns=["year"] + RSHORT).to_csv(f"{DATA}/attacks_by_year_region.csv", index=False)
rows = []
for e in eras:
    for k, h in enumerate(e["hotspots"]):
        rows.append({"era": e["name"], "rank": k + 1, "cell_lat_from": h["lat"], "cell_lon_from": h["lon"], "name": h["name"], "attacks": h["n"], "share_of_era_pct": round(h["pct"], 1)})
pd.DataFrame(rows).to_csv(f"{DATA}/hotspots_by_era.csv", index=False)

# ---------- page data ----------
CN = jload(f"{WORK}/countries.json")
site = {"types": TYPES, "regions": REGIONS, "rshort": RSHORT, "eras": ERAS, "status": STATUS, "cname": CN["cname"], "cpos": CN["cpos"],
        "malacca": MALACCA, "singapore": SINGAPORE}
jsave(site, f"{DATA}/site.json")
DD = D.reset_index(drop=True)
pts, det = [], {}
for i, p in DD.iterrows():
    pts.append([round(p.lat, 3), round(p.lon, 3), int(p.year), int(p.t), int(p.r), int(p.s), round(float(p.shore_km), 1), p.date[5:], p.vessel_name, p.location])
    det[i] = [p.description, p.vessel_type, p.attack_type_raw if isinstance(p.attack_type_raw, str) else "", p.eez_country_name, p.nearest_country_name, 0 if p.year <= 2014 else 1]
jsave({"cols": ["lat", "lon", "year", "type", "region", "status", "shore_km", "month-day", "vessel", "location"], "rows": pts}, f"{DATA}/points.json")
jsave({"cols": ["description", "vessel_type", "attack_type_as_recorded", "eez", "nearest_country", "source(0 MAPPING,1 IMB)"], "rows": [det[i] for i in range(len(DD))]}, f"{DATA}/details.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("peak_year", "peak_n", "mal", "som", "gog", "sin", "ship", "ind_ctx")}, indent=0, cls=NpEnc)[:3000])
print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in R["imb"].items() if k != "sources"})
for f in ("points.json", "details.json", "shipping.json", "site.json", "results.json"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
