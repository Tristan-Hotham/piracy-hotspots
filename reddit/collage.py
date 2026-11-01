"""r/dataisbeautiful collage for piracy-hotspots: 2400 x 3200 px, light background. Numbers from data/results.json.
Small multiples by era (hexagons of attacks over faint shipping lanes), the yearly chart with IMB counts to 2026, and
where piracy is today. Map labels are placed on open sea and checked: a label box must not touch land or any hexagon."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
from shapely.geometry import Polygon as SPoly, box as sbox
from shapely.ops import unary_union

R = jload(f"{DATA}/results.json")
D = attacks()
BGc = "#F7F5F0"; SEAc = "#EAF0F3"; LANDc = "#DEDAD0"; LANE = "#A8C1D4"
HEXC = LinearSegmentedColormap.from_list("hx", ["#FFF0C4", "#FDC46E", "#F08038", "#C83C28", "#82122C", "#3C0828"])
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
EXT = ext_of(-92, -36, 132, 34)
X, Y = proj(D.lon.values, D.lat.values)
GS = (54, 11)                                  # hexagon grid: about 4 degrees across
# shipping lanes for display: the 1 degree AIS density (WORK/shipping_1deg.npy, from 01_clean.py), lightly smoothed
from scipy.ndimage import gaussian_filter
M = np.nan_to_num(np.load(f"{WORK}/shipping_1deg.npy"))
SM = gaussian_filter(np.log1p(M), 1.0)
LEV = list(np.quantile(SM[M > 0], [.85, .93, .98])) + [SM.max() + 1]
glon, glat = np.meshgrid(np.arange(-179.5, 180), 89.5 - np.arange(180))
sel = (glat >= -40) & (glat <= 40)
LX, LYY = proj(glon, glat)

vmax = 0
for k, e in enumerate(R["eras"]):
    m = (D.year >= e["a"]) & (D.year <= e["b"])
    h = plt.figure().add_subplot().hexbin(X[m], Y[m], gridsize=GS, extent=EXT, mincnt=1); vmax = max(vmax, h.get_array().max()); plt.close("all")
H = 3720
fy = lambda px: 1 - px / H                      # pixels from the top -> figure fraction
fh = lambda px: px / H
fig = plt.figure(figsize=(12, H / 200), dpi=200, facecolor=BGc)
fig.text(.045, fy(60), "Where the pirates went", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, fy(212), f"{R['n']:,} pirate attacks on ships, mapped from 1993 to 2020, and where piracy is today. The hotspots moved:\n"
         f"from the South China Sea and Indonesia to Somalia, the Gulf of Guinea and back to the Singapore Strait.",
         fontproperties=SERP, fontsize=13.6, color=FG, va="top", linespacing=1.45)

# ---- small multiples
LAND = []
for iso, ring in SHAPES:
    x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
    if x.max() < EXT[0] or x.min() > EXT[1] or y.max() < EXT[2] or y.min() > EXT[3]:
        continue
    p = SPoly(np.column_stack([x, y])); LAND.append(p if p.is_valid else p.buffer(0))
LANDU = unary_union(LAND)
pw, gap, x0 = .445, .02, .045
PH = pw * 2400 / ((EXT[1] - EXT[0]) / (EXT[3] - EXT[2]))          # panel height in px
NOTE = {0: (f"South China Sea {R['eras'][0]['by_region'][R_SCS]:,} · Indonesia {R['eras'][0]['by_region'][R_IDN]:,}", "#6A3F8C"),
        1: (f"Strait of Malacca peaks: {R['mal']['peak_n']} attacks in {R['mal']['peak_year']}", "#1F7A70"),
        2: (f"Malacca falls to {R['mal']['n_2005']} in 2005 · Somali waters {R['eras'][2]['by_region'][R_SOM]}", FG),
        3: (f"Somali waters {R['som']['n_08_11']:,}: {R['som']['pct_world_08_11']:.0f}% of all attacks", "#9A1B24"),
        4: (f"Singapore Strait {R['eras'][4]['by_region'][R_SIN]} · Somali attacks collapse", "#173F5F"),
        5: (f"Gulf of Guinea {R['gog']['n_16_20']}: {R['gog']['pct_16_20']:.0f}% of all attacks", "#8A6D10")}
norm = LogNorm(1, vmax)
CHECKS = []
ROW0, ROWH = 372, PH + 125
for k, e in enumerate(R["eras"]):
    col, row = k % 2, k // 2
    mt = ROW0 + row * ROWH + 85                     # map top in px
    ax = fig.add_axes([x0 + col * (pw + gap), fy(mt + PH), pw, fh(PH)])
    world(ax, EXT, land=LANDc, ec="#FFFFFF", lw=.25, sea=SEAc)
    ax.contourf(LX, LYY, SM, levels=LEV, colors=["#C7D7E3", "#A9C2D5", "#8EADC6"], zorder=.5, antialiased=True)
    m = (D.year >= e["a"]) & (D.year <= e["b"])
    hb = ax.hexbin(X[m], Y[m], gridsize=GS, extent=EXT, mincnt=1, cmap=HEXC, norm=norm, lw=.4, edgecolors=BGc, zorder=3)
    ax.add_patch(Rectangle((EXT[0], EXT[2]), EXT[1] - EXT[0], EXT[3] - EXT[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))
    fig.text(x0 + col * (pw + gap), fy(mt - 40), e["name"], fontproperties=DISPB, fontsize=19, color=FG, va="bottom")
    fig.text(x0 + col * (pw + gap) + pw, fy(mt - 41), f"{e['n']:,} attacks", fontsize=11, color=MUT, va="bottom", ha="right", family=MONO)
    fig.text(x0 + col * (pw + gap), fy(mt - 10), NOTE[k][0], fontsize=10.6, color=NOTE[k][1], family=MONO, fontweight="medium", va="bottom")
    if k == 0:   # ocean names, first panel only
        for lon, lat, nm in ((-14, -24, "Atlantic\nOcean"), (80, -27, "Indian Ocean")):
            xx, yy = proj(lon, lat)
            CHECKS.append((ax, ax.text(xx, yy, nm, ha="center", va="center", fontsize=10, color="#6F879B", style="italic", family=MONO, zorder=8, path_effects=HALO), hb))

# check labels: no land, no hexagon
fig.canvas.draw(); rend = fig.canvas.get_renderer()
from shapely.geometry import Point
for ax, t, hb in CHECKS:
    bb = t.get_window_extent(rend).transformed(ax.transData.inverted())
    b = sbox(bb.x0, bb.y0, bb.x1, bb.y1)
    assert not b.intersects(LANDU), ("label on land", t.get_text())
    hr = (EXT[1] - EXT[0]) / GS[0] * .62
    assert not [1 for px, py in hb.get_offsets() if b.distance(Point(px, py)) < hr], ("label over a hexagon", t.get_text())

# hexagon and lane legend
LY = ROW0 + 3 * ROWH + 0
fig.text(.045, fy(LY), "Attacks per hexagon (about 4 degrees across), log scale", fontsize=10.5, color=FG, family=MONO, va="bottom")
lx = fig.add_axes([.045, fy(LY + 34), .26, fh(24)]); lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=HEXC, aspect="auto"); lx.set_axis_off()
fig.text(.045, fy(LY + 40), "1", fontsize=10, color=MUT, family=MONO, va="top"); fig.text(.305, fy(LY + 40), f"{int(vmax)}", fontsize=10, color=MUT, family=MONO, va="top", ha="right")
for j, c in enumerate(["#C7D7E3", "#A9C2D5", "#8EADC6"]):
    fig.patches.append(Rectangle((.43 + j * .012, fy(LY + 40)), .012, fh(30), transform=fig.transFigure, fc=c, ec="none"))
fig.text(.47, fy(LY + 25), "Shipping lanes, from World Bank and IMF AIS density\n(2015 to 2021): busiest 15%, 7% and 2% of squares with traffic", fontsize=10.5, color=FG, family=MONO, va="center", linespacing=1.35)

# ---- the yearly chart
CT = LY + 175
fig.text(.045, fy(CT), "Attacks per year, by region, and the IMB's counts since 2020", fontproperties=DISPB, fontsize=19, color=FG, va="bottom")
bx = fig.add_axes([.085, fy(CT + 520), .89, fh(470)]); bx.set_facecolor(BGc)
Yr = np.array(R["years"]); bot = np.zeros(len(Yr))
for i in range(len(REGIONS)):
    bx.bar(Yr[:, 0], Yr[:, i + 1], bottom=bot, width=.86, color=RCOL[i], lw=0); bot += Yr[:, i + 1]
I = R["imb"]
iv = [(2021.6, I["y2021"]), (2022.6, I["y2022"]), (2023.6, I["y2023"]), (2024.6, I["y2024"]), (2025.6, I["y2025"]), (2026.6, I["q3_2026"])]
for xx, v in iv:
    bx.bar(xx, v, width=.86, color="none", edgecolor=MUT, hatch="////", lw=.8, linestyle="--" if xx > 2026 else "-")
bx.axvline(2021.1, color=FG, lw=.8, ls=(0, (3, 3)))
bx.text(2020.9, 540, "mapped", ha="right", fontsize=10, color=MUT, family=MONO); bx.text(2021.3, 540, "IMB counts", fontsize=10, color=MUT, family=MONO)
bx.set_xlim(1992.4, 2027.2); bx.set_ylim(0, 570); spines(bx)
bx.set_xticks([1993, 1997, 2001, 2005, 2009, 2013, 2017, 2020, 2021.6, 2023.6, 2026.6]); bx.set_xticklabels(["1993", "1997", "2001", "2005", "2009", "2013", "2017", "2020", "2021", "2023", "2026*"], fontsize=10.5)
bx.set_yticks(range(0, 501, 100)); bx.tick_params(labelsize=10.5); bx.grid(axis="y", color=RULE, lw=.7); bx.set_axisbelow(True)
ann = lambda x, y, s, c, ha="center": bx.text(x, y, s, ha=ha, va="bottom", fontsize=10.2, color=c, family=MONO, fontweight="medium", linespacing=1.25)
ann(2000, R["by_year"]["2000"] + 8, f"{R['peak_n']} in {R['peak_year']},\nMalacca {R['mal']['peak_n']}", FG)
ann(2010, R["by_year"]["2010"] + 12, f"Somali surge:\n{R['som']['peak_n']} attacks in {R['som']['peak_year']}", "#9A1B24")
ann(2018.4, R["by_year"]["2018"] + 10, f"Gulf of Guinea:\n{R['gog']['pct_2020']:.0f}% in 2020", "#8A6D10")
ann(2025.6, I["y2025"] + 10, f"2025: {I['y2025']},\nSingapore\nStrait {I['sin_2025']}", "#173F5F")
# region legend under the chart, full names
LG = CT + 625
for i, (nm, c) in enumerate(REGIONS):
    cx_, ry = .045 + (i % 2) * .465, LG + (i // 2) * 42
    fig.patches.append(Rectangle((cx_, fy(ry + 9)), .013, fh(18), transform=fig.transFigure, fc=c, ec="none"))
    fig.text(cx_ + .019, fy(ry), nm, fontsize=10.4, color=FG, family=MONO, va="center")
fig.patches.append(Rectangle((.045, fy(LG + 5 * 42 + 9)), .013, fh(18), transform=fig.transFigure, fc="none", ec=MUT, hatch="////", lw=.6))
fig.text(.064, fy(LG + 5 * 42), "IMB headline incident counts, all regions (not mapped points). *2026: January to September only.", fontsize=10.2, color=FG, family=MONO, va="center")

# ---- today
TT = LG + 5 * 42 + 95
fig.text(.045, fy(TT), "Where piracy is now", fontproperties=DISPB, fontsize=19, color=FG, va="bottom")
TILES = [(f"{I['sin_2025']}", "#173F5F", f"incidents in the Singapore\nStrait in 2025, {I['sin_pct_2025']:.0f}% of the\nworld's {I['y2025']} (IMB)"),
         (f"{I['hij_q3_2026']}", "#B3202A", f"hijackings worldwide in Jan\nto Sep 2026, all by Somali\npirates; {R['som']['hij_14_20']} from 2014 to 2020"),
         (f"{I['gog_2025']}", "#A88A12", f"incidents in the Gulf of\nGuinea in 2025, down from\n{R['gog']['peak_n']} mapped in {R['gog']['peak_year']}"),
         (f"{I['q3_2026']}", "#4F5B66", f"incidents worldwide in Jan\nto Sep 2026, {I['q3_drop_pc']:.0f}% fewer than\na year before")]
for k, (big, c, txt) in enumerate(TILES):
    tx0 = .045 + k * .231
    fig.patches.append(Rectangle((tx0, fy(TT + 300)), .215, fh(270), transform=fig.transFigure, fc="#FFFEFA", ec="#D6D0C3", lw=.8))
    fig.patches.append(Rectangle((tx0, fy(TT + 35)), .215, fh(10), transform=fig.transFigure, fc=c, ec="none"))
    fig.text(tx0 + .012, fy(TT + 55), big, fontproperties=DISP, fontsize=30, color=c, va="top")
    fig.text(tx0 + .012, fy(TT + 150), txt, fontsize=9.6, color=FG, family=MONO, va="top", linespacing=1.35)
print("today bottom px", TT + 300, "H", H)
# ---- footer
fig.text(.045, fh(70), "Sources: Benden, Feng, Howell and Dalla Riva (2021), Crime at Sea: A Global Database of Maritime Pirate Attacks 1993 to 2020\n"
         "(from IMB and NGA ASAM reports; CC BY 4.0); ICC International Maritime Bureau press releases, 2021 to 2026; World Bank and IMF\n"
         "Global Shipping Traffic Density (CC BY 4.0); Natural Earth. Reported attacks only: many go unreported.", fontsize=9.6, color=MUT, family=MONO, va="bottom", linespacing=1.45)
fig.text(.045, fh(30), "Analysis and chart: Tristan Hotham, with Python and matplotlib   ·   maps.tristanhotham.com/piracy-hotspots", fontsize=9.6, color=FG, family=MONO, va="bottom")
out = os.path.join(ROOT, "reddit", "pirate_hotspots.png")
fig.savefig(out, dpi=200, facecolor=BGc)
print(out)
