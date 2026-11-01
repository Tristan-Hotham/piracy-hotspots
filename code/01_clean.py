"""Clean the attack database, assign regions, attack types and eras; sum the shipping density raster to 1 degree cells;
tidy the IMB headline counts. Writes data/attacks.csv, data/imb_recent.csv, data/shipping_1deg.csv and
WORK/shipping_1deg.npy."""
import gzip
import numpy as np
import pandas as pd
from common import *

D = pd.read_csv(f"{RAW}/piracy/pirate_attacks.csv", keep_default_na=False, na_values=["NA", ""])
n_raw = len(D)
D["year"] = D.date.str[:4].astype(int)
D["type"] = D.attack_type.map(TYPE_OF).fillna(4).astype(int)
D["status"] = D.vessel_status.fillna("Not recorded").str.strip().str.capitalize().replace({"Underway": "Steaming"})
D["region"] = [region_of(a, b, c if isinstance(c, str) else "", e if isinstance(e, str) else "", f)
               for a, b, c, e, f in zip(D.longitude, D.latitude, D.nearest_country, D.eez_country, D.shore_distance)]
D["era"] = D.year.map(era_of)
D["source"] = D.data_source.map({"mappingpiracy": "MAPPING piracy (IMB and NGA ASAM), 1993 to 2014", "imb": "IMB reports, 2015 to 2020"})
assert D.source.notna().all() and D.era.notna().all()
cc = pd.read_csv(f"{RAW}/piracy/country_codes.csv")
CN = dict(zip(cc.country, cc.country_name))
CN.update({"HKG": "Hong Kong", "TWN": "Taiwan"})
for k in ("nearest_country", "eez_country"):
    D[k + "_name"] = D[k].map(lambda x: CN.get(x, x) if isinstance(x, str) else "")


def clean(s):
    if not isinstance(s, str):
        return ""
    s = dash(re.sub(r"\s+", " ", s.replace("’", "'")).strip())
    return s


out = pd.DataFrame({
    "date": D.date, "year": D.year, "lat": D.latitude.round(4), "lon": D.longitude.round(4),
    "attack_type": [TYPES[t][0] for t in D.type], "attack_type_raw": D.attack_type.fillna(""),
    "vessel_status": D.status, "vessel_type": D.vessel_type.fillna(""), "vessel_name": D.vessel_name.map(clean),
    "region": [REGIONS[r][0] for r in D.region], "era": [ERAS[int(e)][0] for e in D.era],
    "nearest_country": D.nearest_country.fillna(""), "nearest_country_name": D.nearest_country_name,
    "eez_country": D.eez_country.fillna(""), "eez_country_name": D.eez_country_name,
    "shore_km": D.shore_distance.round(2), "location": D.location_description.map(clean),
    "description": D.attack_description.map(clean), "source": D.source})
out.to_csv(f"{DATA}/attacks.csv", index=False)
print("attacks", len(out), "of", n_raw)
print(out.groupby("region").size().sort_values())

# IMB headline counts, 2021 to 2026
I = pd.read_csv(f"{RAW}/piracy/imb_recent.csv")
I["source"] = I.source.map(clean)
I.to_csv(f"{DATA}/imb_recent.csv", index=False)

# shipping density: 0.08 degree overview (a subsample of the 0.005 degree raster), summed to 1 degree cells
raw = gzip.open(f"{RAW}/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz").read()
A = np.frombuffer(raw, dtype="<i4").reshape(2125, 4501).astype(np.float64)
A[A < 0] = 0
# pixel centres: extent lon -180..180, lat 85..-85, north up
lon = -180 + (np.arange(4501) + .5) * 360 / 4501
lat = 85 - (np.arange(2125) + .5) * 170 / 2125
ix = np.clip(np.floor(lon + 180).astype(int), 0, 359)
iy = np.clip(np.floor(90 - lat).astype(int), 0, 179)       # row 0 = 89..90 N
G = np.zeros((180, 360)); N = np.zeros((180, 360))
np.add.at(G, (iy[:, None].repeat(4501, 1), ix[None, :].repeat(2125, 0)), A)
np.add.at(N, (iy[:, None].repeat(4501, 1), ix[None, :].repeat(2125, 0)), 1)
M = np.where(N > 0, G / np.maximum(N, 1), np.nan)        # mean sampled AIS count per overview pixel, per 1 degree cell
np.save(f"{WORK}/shipping_1deg.npy", M)
rows = [(89.5 - r, -179.5 + c, round(M[r, c], 2), int(N[r, c])) for r in range(180) for c in range(360) if N[r, c] > 0 and M[r, c] > 0]
pd.DataFrame(rows, columns=["lat_centre", "lon_centre", "mean_ais_count_per_sample", "samples"]).to_csv(f"{DATA}/shipping_1deg.csv", index=False)
print("shipping cells with traffic", len(rows))
