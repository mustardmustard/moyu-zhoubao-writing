"""
figure_helper.py — make matplotlib render Chinese labels correctly.

matplotlib ships with no CJK font, so Chinese axis/legend text turns into
tofu boxes (□□□) by default. Import and call setup_cjk() BEFORE plotting to
pick whatever CJK font the machine actually has and apply a clean,
report-ready style.

    from figure_helper import setup_cjk
    setup_cjk()
    import matplotlib.pyplot as plt
    ...
    plt.savefig("fig1.png", dpi=300, bbox_inches="tight")

Then reference fig1.png from the .tex (the template already includes it).

Design the chart to look like it belongs in a listed-company annual report:
A4 page width, readable fonts, no chartjunk. Whether the numbers come from the
user's REAL calendar/git log or from an openly-labelled illustrative model,
plot them honestly — don't dress a schematic up as audited operating data.
"""
from matplotlib import font_manager as _fm
import matplotlib as _mpl

# priority list: match the report's serif first, then safe CJK fallbacks
_CJK_PREF = [
    "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "STSong",
    "Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB",
    "Arial Unicode MS", "STHeiti", "Heiti SC", "SimHei", "SimSun",
    "Microsoft YaHei", "WenQuanYi Zen Hei",
]


def available_cjk_font():
    """Return the name of the first installed CJK font, or None."""
    installed = {f.name for f in _fm.fontManager.ttflist}
    for name in _CJK_PREF:
        if name in installed:
            return name
    # last resort: any font whose name hints at CJK
    for f in _fm.fontManager.ttflist:
        if any(k in f.name for k in ("CJK", "Song", "Hei", "Ming", "YaHei", "PingFang", "Gothic")):
            return f.name
    return None


def setup_cjk(base_size: int = 9):
    """Configure matplotlib for clean, CJK-correct, report-ready figures.

    Returns the chosen font name (None if no CJK font was found — Chinese will
    fall back to tofu, so prefer English labels in that case).
    """
    font = available_cjk_font()
    rc = {
        "font.size": base_size,
        "axes.unicode_minus": False,   # render the minus sign, not a box
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "axes.linewidth": 0.8,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "legend.frameon": False,
    }
    if font:
        # put the CJK font at the front of BOTH families so any text renders
        rc["font.sans-serif"] = [font, "DejaVu Sans"]
        rc["font.serif"] = [font, "DejaVu Serif"]
        rc["font.family"] = "sans-serif"
    _mpl.rcParams.update(rc)
    return font


if __name__ == "__main__":
    f = setup_cjk()
    print("CJK font selected:", f or "(none found — use English labels)")
