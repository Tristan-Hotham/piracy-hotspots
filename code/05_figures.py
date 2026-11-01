"""Static figures: header.png (1200 x 630 social card), blog figures (release/blog/b_*.png) and paper figures
(release/paper/f_*.png). All numbers come from data/results.json or data/attacks.csv."""
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter
from figstyle import *

R = jload(f"{DATA}/results.json")
D = attacks()
BL = os.path.join(ROOT, "release", "blog"); PP = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PP, exist_ok=True)
HEXC = LinearSegmentedColormap.from_list("hx", ["#FFF0C4", "#FDC46E", "#F08038", "#C83C28", "#82122C", "#3C0828"])
SEAc, LANDc = "#EAF0F3", "#DEDAD0"
EXT = ext_of(-92, -36, 132, 34)
X, Y = proj(D.lon.values, D.lat.values)
GS = (54, 11)
M = np.nan_to_num(np.load(f"{WORK}/shipping_1deg.npy"))
SM = gaussian_filter(np.log1p(M), 1.0)
LEV = list(np.quantile(SM[M > 0], [.85, .93, .98])) + [SM.max() + 1]
glon, glat = np.meshgrid(np.arange(-179.5, 180), 89.5 - np.arange(180))
LX, LYY = proj(glon, glat)
LANES = ["#C7D7E3", "#A9C2D5", "#8EADC6"]


def vmax_all():
    v = 0
    for e in R["eras"]:
        m = (D.year >= e["a"]) & (D.year <= e["b"])
        f = plt.figure(); h = f.add_subplot().hexbin(X[m], Y[m], gridsize=GS, extent=EXT, mincnt=1); v = max(v, h.get_array().max()); plt.close(f)
    return v


VMAX = vmax_all()
NORM = LogNorm(1, VMAX)


def era_map(ax, a, b, ext=EXT, lanes=True):
    world(ax, ext, land=LANDc, ec="#FFFFFF", lw=.25, sea=SEAc)
    if lanes:
        ax.contourf(LX, LYY, SM, levels=LEV, colors=LANES, zorder=.5)
    m = (D.year >= a) & (D.year <= b)
    ax.hexbin(X[m], Y[m], gridsize=GS, extent=EXT, mincnt=1, cmap=HEXC, norm=NORM, lw=.35, edgecolors=BG, zorder=3)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.add_patch(Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))


def hexlegend(fig, x, y, w=.25):
    lx = fig.add_axes([x, y, w, .012]); lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=HEXC, aspect="auto"); lx.set_axis_off()
    fig.text(x + w / 2, y - .03, "attacks per hexagon (log scale)", fontsize=10, color=FG, va="top", ha="center")
    fig.text(x, y - .006, "1", fontsize=9.5, color=MUT, va="top"); fig.text(x + w, y - .006, f"{int(VMAX)}", fontsize=9.5, color=MUT, va="top", ha="right")


# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(.04, .9, "Pirate hotspots,", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .755, "then and now", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(.04, .6, f"{R['n']:,} attacks on ships mapped, 1993 to 2020, and IMB counts to 2026.\n"
         f"Somali waters peaked at {R['som']['peak_n']} attacks in {R['som']['peak_year']}; the Singapore Strait\nhad {R['imb']['sin_2025']} incidents in 2025.",
         fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.4)
for k, (i, lab) in enumerate(((0, "1993 to 1999"), (3, "2008 to 2011"), (5, "2016 to 2020"))):
    e = R["eras"][i]
    ax = fig.add_axes([.04 + k * .318, .04, .3, .3 / ((EXT[1] - EXT[0]) / (EXT[3] - EXT[2])) * 12 / 6.3])
    era_map(ax, e["a"], e["b"])
    fig.text(.04 + k * .318, .04 + .3 / 2.465 * 12 / 6.3 + .012, lab, fontproperties=DISPB, fontsize=15, color=FG, va="bottom")
fig.text(.96, .9, "maps.tristanhotham.com/piracy-hotspots", fontsize=10, color=MUT, ha="right", va="top")
save(fig, os.path.join(ROOT, "header.png"), dpi=100)

# ---------- small multiples by era ----------
for out, dpi in ((f"{BL}/b_eras.png", 150), (f"{PP}/f_eras.png", 200)):
    fig = plt.figure(figsize=(12, 9.6), facecolor=BG)
    pw = .455; ph = pw * 12 / 9.6 / 2.4655
    for k, e in enumerate(R["eras"]):
        col, row = k % 2, k // 2
        y0 = .955 - (row + 1) * ph - row * .075
        ax = fig.add_axes([.03 + col * (pw + .03), y0, pw, ph]); era_map(ax, e["a"], e["b"])
        fig.text(.03 + col * (pw + .03), y0 + ph + .01, e["name"], fontproperties=DISPB, fontsize=17, color=FG, va="bottom")
        fig.text(.03 + col * (pw + .03) + pw, y0 + ph + .011, f"{e['n']:,} attacks · {RSHORT[e['top_region']]} {e['top_region_pct']:.0f}%", fontsize=10.5, color=MUT, va="bottom", ha="right")
    hexlegend(fig, .03, .055)
    for j, c in enumerate(LANES):
        fig.patches.append(Rectangle((.36 + j * .015, .055), .015, .016, transform=fig.transFigure, fc=c, ec="none"))
    fig.text(.41, .063, "Busy shipping lanes (World Bank and IMF AIS density, 2015 to 2021)", fontsize=10, color=FG, va="center")
    save(fig, out, dpi)

# ---------- attacks per year by region, with IMB counts ----------
for out, dpi in ((f"{BL}/b_years.png", 150), (f"{PP}/f_years.png", 200)):
    fig = plt.figure(figsize=(12, 6.6), facecolor=BG); bx = fig.add_axes([.07, .3, .9, .65]); bx.set_facecolor(BG)
    Yr = np.array(R["years"]); bot = np.zeros(len(Yr))
    for i in range(len(REGIONS)):
        bx.bar(Yr[:, 0], Yr[:, i + 1], bottom=bot, width=.86, color=RCOL[i], lw=0); bot += Yr[:, i + 1]
    I = R["imb"]
    for xx, v in ((2021.6, I["y2021"]), (2022.6, I["y2022"]), (2023.6, I["y2023"]), (2024.6, I["y2024"]), (2025.6, I["y2025"]), (2026.6, I["q3_2026"])):
        bx.bar(xx, v, width=.86, color="none", edgecolor=MUT, hatch="////", lw=.8, linestyle="--" if xx > 2026 else "-")
    bx.axvline(2021.1, color=FG, lw=.8, ls=(0, (3, 3)))
    bx.text(2020.9, 495, "mapped", ha="right", fontsize=10, color=MUT); bx.text(2021.3, 495, "IMB counts", fontsize=10, color=MUT)
    bx.set_xlim(1992.4, 2027.2); bx.set_ylim(0, 520); spines(bx); bx.set_ylabel("attacks per year")
    bx.set_xticks([1993, 1997, 2001, 2005, 2009, 2013, 2017, 2020, 2021.6, 2023.6, 2026.6]); bx.set_xticklabels(["1993", "1997", "2001", "2005", "2009", "2013", "2017", "2020", "2021", "2023", "2026*"])
    bx.grid(axis="y", color=RULE, lw=.7); bx.set_axisbelow(True)
    for i, (nm, c) in enumerate(REGIONS):
        x_, y_ = .07 + (i % 2) * .45, .18 - (i // 2) * .035
        fig.patches.append(Rectangle((x_, y_ - .009), .012, .02, transform=fig.transFigure, fc=c, ec="none"))
        fig.text(x_ + .018, y_, nm, fontsize=10.2, color=FG, va="center")
    fig.text(.07, .005, "Hatched: IMB headline incident counts, all regions, not mapped. *2026: January to September only.", fontsize=9.6, color=MUT, va="bottom")
    save(fig, out, dpi)

# ---------- distance from shore ----------
P = D.copy(); P["t"] = P.year + (pd.to_datetime(P.date).dt.dayofyear / 366)
som = P.region == REGIONS[R_SOM][0]
for out, dpi in ((f"{BL}/b_shore.png", 150), (f"{PP}/f_shore.png", 200)):
    fig = plt.figure(figsize=(12, 6.2), facecolor=BG); ax = fig.add_axes([.08, .12, .9, .82]); ax.set_facecolor(BG)
    ax.scatter(P.t[~som], P.shore_km[~som].clip(.05), s=4, c="#7C8794", alpha=.3, lw=0, label="Everywhere else")
    ax.scatter(P.t[som], P.shore_km[som].clip(.05), s=6, c=HOT, alpha=.5, lw=0, label="Somali coast, Gulf of Aden, Red Sea and Arabian Sea")
    K = R["km_by_year"]
    ax.plot([k[0] + .5 for k in K], [k[2] for k in K], color=FG, lw=2.4, label="Median per year, everywhere else")
    ax.plot([k[0] + .5 for k in K], [np.nan if k[1] is None else k[1] for k in K], color=HOT, lw=2.4, marker="o", ms=5, mec=BG, label="Median per year, Somali waters (five or more attacks)")
    ax.axhline(185.2, color=HOT, ls=(0, (4, 3)), lw=1, alpha=.7); ax.text(1993.2, 205, "100 nautical miles", color=HOT, fontsize=10)
    ax.set_yscale("log"); ax.set_ylim(.05, 1500); ax.set_xlim(1993, 2021); spines(ax); ax.set_ylabel("km from the nearest shore (log scale)")
    ax.set_yticks([.1, 1, 10, 100, 1000]); ax.set_yticklabels(["0.1", "1", "10", "100", "1,000"])
    ax.legend(loc="lower left", fontsize=9.6, frameon=True, facecolor=BG, edgecolor=RULE, ncol=2, markerscale=2)
    save(fig, out, dpi)

# ---------- attack types by era ----------
order = [1, 2, 0, 3, 4]
for out, dpi in ((f"{BL}/b_types.png", 150), (f"{PP}/f_types.png", 200)):
    fig = plt.figure(figsize=(12, 5.4), facecolor=BG); ax = fig.add_axes([.15, .2, .83, .76]); ax.set_facecolor(BG)
    for i, e in enumerate(R["eras"][::-1]):
        left = 0
        for k in order:
            v = 100 * e["by_type"][k] / e["n"]
            ax.barh(i, v, left=left, color=TCOL[k], height=.72, lw=0)
            if v >= 5: ax.text(left + 1, i, f"{v:.0f}%", va="center", color="#fff", fontsize=10.5, fontweight="medium")
            left += v
    ax.set_yticks(range(6)); ax.set_yticklabels([e["name"] for e in R["eras"][::-1]]); ax.set_xlim(0, 100); ax.set_xticks([])
    for s in ax.spines.values(): s.set_visible(False)
    for j, k in enumerate(order):
        fig.patches.append(Rectangle((.06 + j * .18, .06), .012, .035, transform=fig.transFigure, fc=TCOL[k], ec="none"))
        fig.text(.078 + j * .18, .077, TYPES[k][0], fontsize=10.5, color=FG, va="center")
    save(fig, out, dpi)

# ---------- shipping traffic classes ----------
for out, dpi in ((f"{BL}/b_ship.png", 150), (f"{PP}/f_ship.png", 200)):
    B = R["ship"]["bins"]
    fig = plt.figure(figsize=(12, 4.6), facecolor=BG); ax = fig.add_axes([.2, .12, .74, .82]); ax.set_facecolor(BG)
    cols = ["#143A68", "#285480", "#3E6E98", "#6E92B4", "#A3BCD2", "#CCD9E5"]
    for i, b in enumerate(B):
        ax.barh(len(B) - 1 - i, b["attacks_pct"], color=cols[i], height=.68)
        ax.text(b["attacks_pct"] + .5, len(B) - 1 - i, f"{b['attacks_pct']:.1f}%" if b["attacks_pct"] < 1 else f"{b['attacks_pct']:.0f}%", va="center", fontsize=11, fontweight="medium")
    ax.set_yticks(range(len(B))); ax.set_yticklabels([b["name"] + " of squares" for b in B][::-1]); ax.set_xticks([]); ax.set_xlim(0, 42)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Share of all attacks, 1993 to 2020, by how busy their 1 degree square is (AIS traffic, 2015 to 2021)", fontsize=10.5, color=MUT, loc="left")
    save(fig, out, dpi)

# ---------- today: IMB counts ----------
I = R["imb"]
G = [("World total", "#4F5B66", [I["y2023"], I["y2024"], I["y2025"], I["q3_2026"]]), ("Singapore Strait", "#173F5F", [None, I["sin_2024"], I["sin_2025"], I["sin_q3_2026"]]),
     ("Indonesia", "#3E7CB1", [I["idn_2023"], I["idn_2024"], I["idn_2025"], I["idn_q3_2026"]]), ("Gulf of Guinea", "#C9A227", [I["gog_2023"], I["gog_2024"], I["gog_2025"], I["gog_q3_2026"]])]
P4 = ["2023", "2024", "2025", "2026, January to September"]; OP = [.35, .55, .8, 1]
for out, dpi in ((f"{BL}/b_today.png", 150), (f"{PP}/f_today.png", 200)):
    fig = plt.figure(figsize=(12, 5.6), facecolor=BG); ax = fig.add_axes([.06, .2, .92, .74]); ax.set_facecolor(BG)
    for g, (n, c, vs) in enumerate(G):
        for k, v in enumerate(vs):
            x = g + (k - 1.5) * .2
            if v is None:
                ax.text(x, 2, "n/a", ha="center", fontsize=9, color=MUT); continue
            ax.bar(x, v, width=.18, color=c, alpha=OP[k], lw=0); ax.text(x, v + 2, str(v), ha="center", fontsize=10.5)
    ax.set_xticks(range(4)); ax.set_xticklabels([g[0] for g in G], fontsize=11.5); spines(ax); ax.set_ylim(0, 150); ax.grid(axis="y", color=RULE, lw=.7); ax.set_axisbelow(True)
    ax.set_ylabel("incidents reported to the IMB")
    for k, p in enumerate(P4):
        fig.patches.append(Rectangle((.06 + k * .2, .05), .012, .035, transform=fig.transFigure, fc="#4F5B66", alpha=OP[k], ec="none"))
        fig.text(.078 + k * .2, .067, p, fontsize=10.2, va="center")
    save(fig, out, dpi)

# ---------- paper only: country income and attacks (correlation, not cause) ----------
C = pd.read_csv(f"{WORK}/ctry_ind.csv")
cc = pd.read_csv(f"{RAW}/piracy/country_codes.csv"); CN = dict(zip(cc.country, cc.country_name))
fig = plt.figure(figsize=(10, 6.4), facecolor=BG); ax = fig.add_axes([.1, .12, .86, .82]); ax.set_facecolor(BG)
ax.scatter(C.gdp, C.n, s=26, c=COOL, alpha=.75, lw=.4, edgecolor="#fff")
for _, r in C.sort_values("n", ascending=False).head(10).iterrows():
    nm = CN.get(r.eez_country, r.eez_country).replace(", Rep.", "").replace(", RB", "").replace(", Fed. Rep.", "")
    ax.annotate(nm, (r.gdp, r.n), xytext=(6, 2), textcoords="offset points", fontsize=9.5)
ax.set_xscale("log"); ax.set_yscale("log"); spines(ax)
ax.set_xlabel("median GDP per person in the years with attacks (US dollars, log scale)"); ax.set_ylabel("attacks in the country's EEZ, 1993 to 2019 (log)")
save(fig, f"{PP}/f_income.png", 200)
print("figures done; vmax", VMAX)
