"""fig_layouts.py — 배치 A · B · C 를 위에서 본 그림 (배치 뽑기 lab/common_dr_sampler.py 를 Isaac 없이 그대로 씀).
    python3 fig_layouts.py <Medical_bio_experiment 경로>
"""
import os
import sys

import numpy as np

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/Medical_bio_experiment"
sys.path.insert(0, os.path.join(ROOT, "lab"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pstyle as S
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
import common_dr_sampler as D

N = 300
ASSETS = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "usd")
BASE = np.array([-0.66, 0.0])          # 로봇 받침 (world xy) — FR3 · FR5 같은 자리


def sample(mode, seed):
    D.set_layout_mode(mode)
    C = D.load_configs(os.path.join(ROOT, "config"), "franka", assets_dir=ASSETS)
    sm = D.LayoutSampler(C, log=lambda *x: None)
    out = []
    for i in range(N):
        rng = np.random.default_rng([seed, i])
        sm.force_ring = sm.ring_holes[i % len(sm.ring_holes)]
        if sm.mode == "B":
            nsp, nrk = len(sm.b_spacings), len(sm.b_racks)
            sm.force_b = {"spacing": sm.b_spacings[i % nsp], "ring_rack": sm.b_racks[(i // nsp) % nrk], "pair": i // (nsp * nrk), "ring_pick": i // (nsp * nrk * 3)}
        lay = sm.sample(rng)
        if not lay.get("fallback"):
            out.append(lay)
    return sm, C, out


def P(xy):
    """world xy → 그림 (가로 = −y_base, 세로 = x_base), mm."""
    v = (np.asarray(xy, float)[..., :2] - BASE) * 1000.0
    return np.stack([-v[..., 1], v[..., 0]], axis=-1)


def draw_rack(ax, sm, geom, xy, yaw, lw=0.8, fc="white", ec=S.G1, z=3):
    c = P(geom.corners_xy(np.array(xy), yaw))
    ax.add_patch(Polygon(c, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))
    for h in P(geom.holes_xy(np.array(xy), yaw)):
        ax.add_patch(Circle(h, 15.5, fc="white", ec=S.G2, lw=0.4, zorder=z + 0.1))


def draw_layout(ax, sm, lay):
    draw_rack(ax, sm, sm.g, lay["holder"]["xy"], lay["holder"]["yaw_deg"])
    d = lay["dest"]
    draw_rack(ax, sm, sm.bk, d["xy"], d["yaw_deg"], fc="#F2F2F2")
    for col, c in (("red", S.CRED), ("yellow", S.CYEL)):
        t = lay["tubes"][col]
        ax.add_patch(Circle(P(t["xy"]), 15.0, fc=c, ec=S.G1, lw=0.5, zorder=5))
    ax.add_patch(Circle(P(d["ring_xy"]), 20.5, fc="none", ec=S.CRED, lw=1.4, zorder=6))


def frame(ax, C, sm):
    x0, x1, y0, y1 = sm.desk_box
    c = P(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]))
    ax.add_patch(Polygon(c, closed=True, fc="none", ec=S.G3, lw=0.6, ls=(0, (3, 2)), zorder=1))
    ax.add_patch(Circle((0, 0), 60, fc=S.G1, ec="none", zorder=4))
    ax.text(80, 0, T("로봇 받침", "robot base"), ha="left", va="center", fontsize=6.3)
    for r, col in (("franka", S.C3), ("fr5", S.C5)):
        pos, R = D.third_cam_world(C[r])
        p = P(pos[:2])
        f = R[:2, 2] * -1.0                                   # 카메라 앞 방향 (OpenGL −z)
        fv = np.array([-f[1], f[0]])
        if p[1] > 1000:                                       # FR3 카메라는 그림 위쪽 밖 (x 1.26 m) — 가장자리에 표시
            ax.plot(p[0], 985, marker="^", ms=4.5, color=col, zorder=6, clip_on=False)
            ax.text(p[0] - 30, 985, "x=%.0f" % p[1], fontsize=5.6, color=col, va="center", ha="right")
        else:
            ax.plot(*p, marker="v", ms=4.5, color=col, zorder=6, clip_on=False)
    ax.set_aspect("equal")
    ax.set_xlim(-560, 560)
    ax.set_ylim(-150, 1000)
    ax.set_xticks([-400, 0, 400])
    ax.set_yticks([0, 400, 800])
    ax.tick_params(length=2)


def T(ko, en):
    return S.T(ko, en)


def main():
    res = {m: sample(m, s) for m, s in (("A", 1103), ("B", 1105), ("C", 7700))}
    for lang in ("ko", "en"):
        S.set_lang(lang)
        fig, axs = plt.subplots(1, 3, figsize=(S.COL2, 2.75), sharey=True)
        for ax, (m, (sm, C, lays)) in zip(axs, res.items()):
            frame(ax, C, sm)
            hc = P(np.array([l["holder"]["xy"] for l in lays]))
            dc = P(np.array([l["dest"]["xy"] for l in lays]))
            if m != "C":
                ax.scatter(hc[:, 0], hc[:, 1], s=2.0, c=S.G2, lw=0, zorder=2, label=T("원래 랙 중심", "source rack centre"))
                ax.scatter(dc[:, 0], dc[:, 1], s=4.0, facecolors="none", edgecolors=S.G2, lw=0.35, zorder=2, label=T("빈 랙 중심", "empty rack centre"))
            ex = lays[3] if m != "C" else lays[0]
            draw_layout(ax, sm, ex)
            if m == "C":
                other = next(l for l in lays if l["red_side"] != ex["red_side"])
                ax.add_patch(Circle(P(other["tubes"]["red"]["xy"]), 15.0, fc="none", ec=S.CRED, lw=0.9, ls=(0, (2, 1.2)), zorder=6))
                for l in lays:
                    ax.add_patch(Circle(P(l["dest"]["ring_xy"]), 20.5, fc="none", ec=S.CRED, lw=0.5, ls=(0, (2, 1.2)), zorder=5))
            title = {"A": T("A: 랙 무작위, 튜브 양 끝", "A: random racks, tubes at ends"),
                     "B": T("B: 랙 무작위, 튜브 아무 구멍", "B: random racks, tubes in any holes"),
                     "C": T("C: 고정 랙, 빨강 좌우 번갈아", "C: fixed racks, red end alternates")}[m]
            ax.set_title(title, fontsize=7.3, pad=3)
            ax.set_xlabel("\u2212y (mm)")
            print("[layouts] %s: %d / %d" % (m, len(lays), N))
        axs[0].set_ylabel("x (mm)")
        h = [plt.Line2D([], [], ls="", marker="o", ms=3, color=S.G2), plt.Line2D([], [], ls="", marker="o", ms=3.5, mfc="none", mec=S.G2),
             plt.Line2D([], [], ls="", marker="o", ms=5, mfc=S.CRED, mec=S.G1), plt.Line2D([], [], ls="", marker="o", ms=5, mfc=S.CYEL, mec=S.G1),
             plt.Line2D([], [], ls="", marker="o", ms=6.5, mfc="none", mec=S.CRED, mew=1.3),
             plt.Line2D([], [], ls="", marker="v", ms=4.5, color=S.C3), plt.Line2D([], [], ls="", marker="v", ms=4.5, color=S.C5)]
        lab = [T("원래 랙 중심", "source-rack centre"), T("빈 랙 중심", "empty-rack centre"), T("빨간 튜브", "red tube"), T("노란 튜브", "yellow tube"),
               T("빨간 링 (목표)", "red ring (goal)"), T("FR3 3인칭 카메라", "FR3 third-person cam."), T("FR5 3인칭 카메라", "FR5 third-person cam.")]
        fig.legend(h, lab, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1), handletextpad=0.3, columnspacing=1.2)
        fig.subplots_adjust(wspace=0.08, bottom=0.2)
        S.save(fig, "fig_layouts")


if __name__ == "__main__":
    main()
