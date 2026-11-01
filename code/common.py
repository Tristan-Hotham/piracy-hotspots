"""Shared paths, groupings and helpers for the piracy-hotspots project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw6/piracy/pirate_attacks.csv
      Crime at Sea: A Global Database of Maritime Pirate Attacks (1993 to 2020), Benden, Feng, Howell and Dalla Riva (2021),
      Journal of Open Humanities Data 7: 19, https://doi.org/10.5334/johd.39, as published in the GitHub repository
      newzealandpaul/Maritime-Pirate-Attacks (CC BY 4.0). 7,511 attacks with date, position, attack type, vessel type and
      status, nearest country, EEZ country, distance to shore and source (1993 to 2014 from the MAPPING piracy data of
      Brandon Prins, which compiles IMB and NGA ASAM reports; 2015 to 2020 from IMB reports).
  /home/claude/newdata/raw6/piracy/country_indicators.csv, country_codes.csv
      Country indicators by year from the same repository (World Bank and others; CC BY 4.0 as published there).
  /home/claude/newdata/raw6/piracy/imb_recent.csv
      Headline counts from the ICC International Maritime Bureau (IMB) Piracy Reporting Centre's annual and quarterly
      press releases, 2021 to January to September 2026, transcribed with their source notes and URLs.
  /home/claude/newdata/raw6/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz
      World Bank / IMF Global Shipping Traffic Density (AIS, January 2015 to February 2021; CC BY 4.0), the 0.08 degree
      overview of the all-vessels raster. The overview is a subsample, so it is only used summed to 1 degree cells.
  /home/claude/newdata/raw/geo/  Natural Earth countries, land and populated places (public domain).
"""
import json, gzip, os, re
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PIR_RAW", "/home/claude/newdata/raw6")
GEO = os.environ.get("PIR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PIR_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("PIRTMP", "/dev/shm/piracy"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "piracy-hotspots"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23856383"                 # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/piracy-hotspots/"           # filled in by the publisher
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# attack types (order = legend order); the source uses both "Boarded" and "Boarding" for the same thing in alternate years
TYPES = [("Boarded", "#2F7FB8"), ("Hijacked", "#B3202A"), ("Fired upon", "#E07B24"), ("Attempted", "#8A6FB5"),
         ("Other or not recorded", "#B9B3A6")]
TYPE_OF = {"Boarded": 0, "Boarding": 0, "Hijacked": 1, "Fired Upon": 2, "Attempted": 3}

# regions (order = legend order). Assigned by simple geography, in the order set out in region_of() below.
REGIONS = [("Gulf of Guinea and West Africa", "#C9A227"),
           ("Somali coast, Gulf of Aden, Red Sea and Arabian Sea", "#B3202A"),
           ("East African coast: Kenya to South Africa", "#E8909A"),
           ("Indian subcontinent", "#E07B24"),
           ("Strait of Malacca", "#2A9D8F"),
           ("Singapore Strait", "#173F5F"),
           ("Indonesia", "#3E7CB1"),
           ("South China Sea, Philippines and East Asia", "#7A4E9C"),
           ("Americas", "#5E8C4A"),
           ("Elsewhere", "#9C9488")]
RSHORT = ["Gulf of Guinea", "Somali waters", "East Africa", "Indian subcontinent", "Malacca Strait", "Singapore Strait",
          "Indonesia", "South China Sea", "Americas", "Elsewhere"]
R_GOG, R_SOM, R_EAF, R_IND, R_MAL, R_SIN, R_IDN, R_SCS, R_AME, R_OTH = range(10)

# eras for the small multiples, hotspot tables and page buttons
ERAS = [("1993 to 1999", 1993, 1999), ("2000 to 2004", 2000, 2004), ("2005 to 2007", 2005, 2007),
        ("2008 to 2011", 2008, 2011), ("2012 to 2015", 2012, 2015), ("2016 to 2020", 2016, 2020)]

# Strait of Malacca: a polygon from the Andaman Sea entrance to the western end of the Singapore Strait (lon, lat)
MALACCA = [(95.2, 5.6), (95.6, 6.3), (98.0, 6.6), (100.3, 6.6), (100.6, 4.6), (101.4, 2.95), (102.7, 2.05), (103.42, 1.5),
           (103.42, 0.6), (102.3, 0.6), (101.0, 1.6), (100.0, 2.4), (98.6, 3.5), (97.4, 4.6)]
SINGAPORE = (103.42, 0.85, 104.65, 1.60)     # lon0, lat0, lon1, lat1: Singapore Strait incl. Batam and Bintan anchorages
SCS_ISO = {"MYS", "SGP", "THA", "VNM", "KHM", "PHL", "CHN", "HKG", "MAC", "TWN", "BRN", "MMR", "JPN", "KOR", "PRK", "PNG",
           "SLB", "RUS"}
IND_ISO = {"IND", "BGD", "LKA", "PAK", "MDV"}
EAF_ISO = {"KEN", "TZA", "MOZ", "MDG", "COM", "ZAF", "MUS", "MYT", "REU"}


STATUS = ["Anchored", "Berthed", "Steaming", "Other", "Not recorded"]

# names for 1 degree hotspot cells (south-west corner lat, lon), from the location descriptions of the attacks in them
CELLNAME = {(22, 91): "Chittagong anchorages, Bangladesh", (-7, 106): "Jakarta and Tanjung Priok, Indonesia",
            (3, 98): "Belawan, Sumatra, Indonesia", (-3, 107): "Gelasa Strait and Bangka, Indonesia",
            (22, 114): "Hong Kong waters", (-23, -44): "Rio de Janeiro, Brazil", (13, 100): "Bangkok Bar and Laem Chabang, Thailand",
            (6, 79): "Colombo, Sri Lanka", (-6, 105): "Panjang, Sumatra, Indonesia", (-1, 117): "Samarinda and Muara Berau, Indonesia",
            (6, 3): "Lagos anchorages, Nigeria", (-2, 116): "Balikpapan, Indonesia", (1, 102): "Malacca Strait off Tanjung Tohor",
            (13, 80): "Chennai, India", (1, 104): "Singapore Strait, eastern part", (1, 103): "Singapore Strait, western part",
            (-7, 39): "Dar es Salaam, Tanzania", (-13, -78): "Callao, Peru", (10, 107): "Vung Tau, Vietnam",
            (13, 49): "Gulf of Aden, central", (13, 48): "Gulf of Aden, west of centre", (3, 105): "Pulau Mangkai, South China Sea",
            (13, 42): "Southern Red Sea, off Assab", (12, 47): "Gulf of Aden, Somali side", (12, 43): "Bab el Mandeb strait",
            (1, 101): "Dumai, Sumatra, Indonesia", (-4, 114): "Taboneo, Kalimantan, Indonesia", (-5, 11): "Pointe Noire, Congo",
            (6, 1): "Lome, Togo", (3, 6): "Niger Delta offshore, Nigeria", (10, -65): "Puerto La Cruz and Jose, Venezuela",
            (4, -2): "Takoradi, Ghana"}


def in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def region_of(lon, lat, near, eez, dist):
    """Region of one attack: first rule that applies."""
    a, b, c, d = SINGAPORE
    if a <= lon <= c and b <= lat <= d:
        return R_SIN
    if in_poly(lon, lat, MALACCA):
        return R_MAL
    if near in ("IDN", "TLS") or eez in ("IDN", "TLS"):
        return R_IDN
    if 90 <= lon <= 160 and -12 <= lat <= 50 and (near in SCS_ISO or eez in SCS_ISO):
        return R_SCS
    if near in IND_ISO and dist < 300:
        return R_IND
    if near in EAF_ISO and dist < 60:
        return R_EAF
    if 32 <= lon <= 80 and -15 <= lat <= 30 and not (lat > 24.3 and 47 <= lon <= 57.5):
        return R_SOM
    if -30 <= lon <= 16 and -20 <= lat <= 20:
        return R_GOG
    if lon < -30:
        return R_AME
    return R_OTH


def era_of(y):
    for i, (n, a, b) in enumerate(ERAS):
        if a <= y <= b:
            return i
    return None


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", " - ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


class NpEnc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer): return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        return super().default(o)


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(json.loads(json.dumps(obj, cls=NpEnc)))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), cls=NpEnc)


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    raise ValueError(f)
