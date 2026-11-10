"""pstyle.py — 논문 그림 공용 모양 (흑백 + 강조색). 그림 스크립트가 import 함."""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figs")
C3 = "#0072B2"      # FR3
C5 = "#D55E00"      # FR5
CE = "#009E73"      # 강조
CRED = "#B2182B"    # 빨간 튜브 (장면 속 물체 색 — 그 그림에서만)
CYEL = "#E6AB02"    # 노란 튜브
G1, G2, G3 = "#222222", "#777777", "#BBBBBB"
ROBOT_C = {"fr3": C3, "franka": C3, "fr5": C5}
COL1 = 3.35          # 한 단 폭 (inch, 85 mm)
COL2 = 6.85          # 두 단 폭 (inch, 174 mm)

for p in glob.glob("/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-*.otf"):
    try:
        fm.fontManager.addfont(p)
    except Exception:
        pass
for p in glob.glob("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc") + glob.glob("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
    try:
        fm.fontManager.addfont(p)
    except Exception:
        pass

LANG = "en"


def set_lang(lang):
    global LANG
    LANG = lang
    fam = ["TeX Gyre Heros", "Noto Sans CJK KR", "DejaVu Sans"] if lang == "en" else ["TeX Gyre Heros", "Noto Sans CJK KR", "DejaVu Sans"]
    plt.rcParams.update({
        "font.family": fam,
        "font.size": 7.5,
        "axes.titlesize": 8,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "legend.fontsize": 6.8,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": G1,
        "axes.labelcolor": G1,
        "xtick.color": G1,
        "ytick.color": G1,
        "text.color": G1,
        "axes.grid": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 300,
        "axes.unicode_minus": False,
        "mathtext.fontset": "custom",
        "mathtext.rm": "TeX Gyre Heros",
        "mathtext.it": "TeX Gyre Heros:italic",
    })


def T(ko, en):
    return ko if LANG == "ko" else en


PGF_PRE = "\n".join([
    r"\usepackage{fontspec}",
    r"\setmainfont{TeX Gyre Heros}",
    r"\setsansfont{TeX Gyre Heros}",
    r"\newfontfamily\krfont{Noto Sans CJK KR}[Scale=0.92]",
    r"\usepackage[Latin,Korean]{ucharclasses}",
    r"\makeatletter\def\kr@prev{\familydefault}\def\kron{\edef\kr@prev{\f@family}\krfont}\def\kroff{\fontfamily{\kr@prev}\selectfont}\makeatother",
    r"\setTransitionsForKorean{\kron}{\kroff}",
    r"\usepackage{amsmath}",
])


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, "%s_%s" % (name, LANG))
    with plt.rc_context({"pgf.texsystem": "xelatex", "pgf.rcfonts": False, "pgf.preamble": PGF_PRE, "font.family": "sans-serif"}):
        fig.savefig(base + ".pdf", bbox_inches="tight", pad_inches=0.02, backend="pgf")
    import subprocess
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", base + ".pdf", base], check=False)
    plt.close(fig)
    print("[fig] %s.pdf · .png" % base)


def panel(ax, s):
    ax.text(-0.02, 1.02, s, transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, fontweight="bold")
