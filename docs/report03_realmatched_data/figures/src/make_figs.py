"""make_figs.py — 데이터 그림 (한 · 영). analyze.py 가 만든 stats.json 과 내보낸 기록을 씀.
    python3 make_figs.py <paper_export_1110> <stats.json> [그림 이름 ...]
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pstyle as S
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

EX, SP = sys.argv[1], sys.argv[2]
ONLY = set(sys.argv[3:])
ST = json.load(open(SP))
EQ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(SP)), "matched_equal_n.json")))   # equal_n.py — 같은 장면 · 같은 판 수
T = S.T
DS = ["AB100", "AB_A200", "AB_B", "ab_A", "ab_B"]
DSL = {"AB100": "AB 100", "AB_A200": "AB A+200", "AB_B": "AB B", "ab_A": "ab A", "ab_B": "ab B"}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def ecdf(ax, x, color, label, ls="-"):
    x = np.sort(np.asarray(x, float))
    y = np.arange(1, len(x) + 1) / len(x)
    ax.step(x, y, where="post", color=color, lw=1.1, ls=ls, label=label)


# ------------------------------------------------------------------ 수학 모델: 성공률 · 버림 · 정밀도
def fig_mathmodel():
    fig, axs = plt.subplots(1, 4, figsize=(S.COL2, 1.95), gridspec_kw={"width_ratios": [1.25, 1.0, 1.0, 1.0]})
    ax = axs[0]
    for j, rb in enumerate(("fr3", "fr5")):
        for i, d in enumerate(DS):
            x = EQ["sets"][d]
            p = 100.0 * x[rb] / x["n"]
            lo, hi = x[rb + "_ci"]
            xx = i + (-0.13 if rb == "fr3" else 0.13)
            ax.errorbar(xx, p, yerr=[[max(0, p - lo)], [max(0, hi - p)]], fmt="o", ms=3.2, color=S.ROBOT_C[rb], elinewidth=0.8, capsize=1.6, mew=0)
    ax.axvspan(2.5, 4.5, color="#F0F0F0", zorder=0, lw=0)
    ax.text(3.5, 69.6, T("실물 설정", "real-matched"), ha="center", fontsize=6.0, color=S.G2)
    ax.set_xticks(range(len(DS)))
    ax.set_xticklabels(["%s (%d)" % (DSL[d], EQ["sets"][d]["n"]) for d in DS], rotation=35, ha="right")
    ax.set_ylim(68, 101)
    ax.set_ylabel(T("같은 장면 첫 시도 성공 (%)", "first-attempt success, same scenes (%)"))
    S.panel(ax, "a")
    # (b) 같은 장면 첫 시도의 실패 까닭 (다섯 묶음 합, 두 로봇 같은 장면 수)
    ax = axs[1]
    kinds = [("slip", T("손에서 벗어남", "slipped in hand"), S.CE), ("not_in_hole", T("구멍에 없음", "not in hole"), S.G1),
             ("shallow", T("덜 꽂힘", "shallow"), S.G2), ("other", T("기타", "other"), S.G3), ("noplan", T("계획 못 함", "cannot plan"), "#D9D9D9")]
    G = EQ["groups"]["all"]
    tot = {}
    for rb in ("fr3", "fr5"):
        c = {}
        for k, v in G[rb + "_first_why"].items():
            kk = k if k in ("slip", "not_in_hole", "shallow") else "other"
            c[kk] = c.get(kk, 0) + v
        if rb == "fr5":
            c["noplan"] = G["fr5_noplan"]
        tot[rb] = c
    att = {rb: G["n"] for rb in ("fr3", "fr5")}
    for i, rb in enumerate(("fr3", "fr5")):
        left = 0
        for k, lab, col in kinds:
            v = tot[rb].get(k, 0)
            if v:
                ax.barh(i, v, left=left, color=col, height=0.42, edgecolor="white", lw=0.6)
            left += v
        ax.text(left + 4, i, "%d / %s" % (left, "{:,}".format(att[rb])), va="center", fontsize=6.0)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["FR3", "FR5"])
    for t, rb in zip(ax.get_yticklabels(), ("fr3", "fr5")):
        t.set_color(S.ROBOT_C[rb])
    ax.set_xlim(0, 215)
    ax.set_ylim(3.2, -0.5)
    ax.set_xlabel(T("첫 시도 실패 (같은 장면)", "first-attempt failures"))
    ax.legend([Rectangle((0, 0), 1, 1, color=c) for _, _, c in kinds], [l for _, l, _ in kinds], loc="lower right", bbox_to_anchor=(1.02, 0.0), fontsize=5.6, handlelength=0.9, handletextpad=0.3, borderaxespad=0.1)
    S.panel(ax, "b")
    # (c) d_ax ECDF, (d) 기울기 ECDF (저장된 시연, 모든 묶음)
    for ax, key, xl, thr, lim, pn in ((axs[2], "dax_raw", T("턱 높이에서 축 거리 (mm)", "axis offset at rim $d_{ax}$ (mm)"), 2.0, (0, 2.3), "c"),
                                      (axs[3], "tilt_raw", T("튜브 기울기 (°)", "tube tilt (°)"), 12.0, (0, 5), "d")):
        for rb in ("fr3", "fr5"):
            v = sum((ST["auto"][d][rb][key] for d in DS), [])
            ecdf(ax, v, S.ROBOT_C[rb], "FR3" if rb == "fr3" else "FR5")
        if thr <= lim[1]:
            ax.axvline(thr, color=S.G1, ls=(0, (3, 2)), lw=0.8)
            ax.text(thr - 0.04, 0.05, T("성공 기준", "threshold"), rotation=90, ha="right", va="bottom", fontsize=5.8)
        else:
            ax.text(lim[1] * 0.97, 0.05, T("성공 기준 12°", "threshold 12°") + " →", ha="right", va="bottom", fontsize=5.8)
        ax.set_xlim(*lim)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel(xl)
        ax.set_ylabel(T("누적 비율", "cumulative fraction") if pn == "c" else "")
        if pn == "c":
            ax.legend(loc="center left", bbox_to_anchor=(0.42, 0.4), handlelength=1.2, borderaxespad=0.1)
        S.panel(ax, pn)
    fig.subplots_adjust(wspace=0.55)
    S.save(fig, "fig_mathmodel")


# ------------------------------------------------------------------ 같은 장면 두 로봇 궤적
def load_pair():
    F3 = os.path.join(EX, "text", "fr3", "018_20261107_ab_a_1103", "progress", "episodes.jsonl")
    F5 = os.path.join(EX, "text", "fr5", "016_20261107_ab_a_1103", "progress", "episodes.jsonl")
    E3 = {r["episode_index"]: r for r in jl(F3)}
    E5 = {r["episode_index"]: r for r in jl(F5)}
    z3 = np.load(os.path.join(EX, "traj", "fr3__018_20261107_ab_a_1103.npz"))
    z5 = np.load(os.path.join(EX, "traj", "fr5__016_20261107_ab_a_1103.npz"))
    full3 = {int(z3["full_ep_%d" % i]): (z3["full_s_%d" % i], z3["full_a_%d" % i]) for i in range(6) if "full_ep_%d" % i in z3.files}
    full5 = {int(z5["full_ep_%d" % i]): (z5["full_s_%d" % i], z5["full_a_%d" % i]) for i in range(6) if "full_ep_%d" % i in z5.files}
    pid3 = {E3[k]["pair_id"]: k for k in full3 if k in E3}
    pid5 = {E5[k]["pair_id"]: k for k in full5 if k in E5}
    common = [p for p in pid3 if p in pid5]
    p = "1103-5" if "1103-5" in common else common[0]
    return p, E3[pid3[p]], E5[pid5[p]], full3[pid3[p]], full5[pid5[p]]


ST_ORDER = [("approach", ["튜브로 가기"], T), ("grasp", ["쥐기 전 멈춤", "쥐기", "쥔 채 기다림"], T), ("carry", ["옮기기"], T),
            ("align", ["구멍 위에서 멈춤", "구멍 맞추기"], T), ("insert", ["꽂기 전 멈춤", "꽂기"], T),
            ("release", ["놓기 전 멈춤", "놓기", "놓은 뒤 멈춤"], T), ("retreat", ["위로 빠지기"], T)]
STN = {n: s for s, ns, _ in ST_ORDER for n in ns}


def stname(k):
    return {"approach": T("다가가기", "approach"), "grasp": T("쥐기", "grasp"), "carry": T("옮기기", "carry"), "align": T("맞추기", "align"),
            "insert": T("꽂기", "insert"), "release": T("놓기", "release"), "retreat": T("빠지기", "retreat")}[k]


def segs(rec):
    tl = rec["input_stats"]["auto"]["timeline"]
    n = rec["length"]
    out = []
    for i, (name, k0) in enumerate(tl):
        k1 = tl[i + 1][1] if i + 1 < len(tl) else n
        s = STN.get(name)
        if s is None:
            continue
        if out and out[-1][0] == s:
            out[-1][2] = k1
        else:
            out.append([s, k0, k1])
    return out


def yaw_of(s):
    return np.degrees(np.unwrap(np.arctan2(s[:, 6].astype(float), s[:, 3].astype(float))))


def fig_traj():
    p, r3, r5, (s3, a3), (s5, a5) = load_pair()
    lim3 = np.radians(r3["input_stats"]["auto"]["limits"]["franka"]["vmax_deg_s"])
    lim5 = np.radians(r5["input_stats"]["auto"]["limits"]["fr5"]["vmax_deg_s"])
    fig = plt.figure(figsize=(S.COL2, 2.3))
    gs = fig.add_gridspec(2, 4, width_ratios=[1.25, 1.3, 1.3, 1.3], height_ratios=[1, 1], wspace=0.5, hspace=0.22)
    ax0 = fig.add_subplot(gs[:, 0])
    m = r3["input_stats"]["auto"]["scene_measured"]
    for (s, rb, r) in ((s3, "fr3", r3), (s5, "fr5", r5)):
        ax0.plot(-s[:, 1] * 1000, s[:, 0] * 1000, color=S.ROBOT_C[rb], lw=1.0)
        ax0.plot(-s[0, 1] * 1000, s[0, 0] * 1000, "o", ms=3, mfc="white", mec=S.ROBOT_C[rb], mew=0.8)
    b = m["tube_bottom"]
    ax0.plot(-b[1] * 1000, b[0] * 1000, "o", ms=4.2, color=S.CRED, mec=S.G1, mew=0.4, zorder=5)
    h = m["hole_xy"]
    ax0.plot(-h[1] * 1000, h[0] * 1000, "o", ms=6.5, mfc="none", mec=S.CRED, mew=1.2, zorder=5)
    allx = np.concatenate([-s3[:, 1], -s5[:, 1]]) * 1000
    ally = np.concatenate([s3[:, 0], s5[:, 0]]) * 1000
    cx, cy = (allx.min() + allx.max()) / 2, (ally.min() + ally.max()) / 2
    hs = max(allx.max() - allx.min(), ally.max() - ally.min()) / 2 + 22
    ax0.set_xlim(cx - hs, cx + hs)
    ax0.set_ylim(cy - hs, cy + hs)
    ax0.set_aspect("equal")
    ax0.set_xlabel("−y (mm)")
    ax0.set_ylabel("x (mm)")
    ax0.set_title(T("손끝 길 (위에서)", "TCP path (top)"), fontsize=7)
    ax0.legend([Line2D([], [], color=S.C3), Line2D([], [], color=S.C5), Line2D([], [], ls="", marker="o", ms=3, mfc="white", mec=S.G1),
                Line2D([], [], ls="", marker="o", ms=3.5, color=S.CRED), Line2D([], [], ls="", marker="o", ms=5, mfc="none", mec=S.CRED, mew=1.1)],
               ["FR3", "FR5", T("시작", "start"), T("빨간 튜브", "red tube"), T("목표 구멍", "goal hole")], fontsize=5.4, loc="upper center",
               bbox_to_anchor=(0.45, -0.32), ncol=2, handletextpad=0.2, columnspacing=0.5, borderaxespad=0.2, handlelength=1.4)
    S.panel(ax0, "a")
    for row, (s, a, r, rb, lim) in enumerate(((s3, a3, r3, "fr3", lim3), (s5, a5, r5, "fr5", lim5))):
        t = np.arange(len(s)) / 30.0
        col = S.ROBOT_C[rb]
        ax1 = fig.add_subplot(gs[row, 1])
        ax2 = fig.add_subplot(gs[row, 2], sharex=ax1)
        ax3 = fig.add_subplot(gs[row, 3], sharex=ax1)
        sg = segs(r)
        for ax in (ax1, ax2, ax3):
            for i, (k, k0, k1) in enumerate(sg):
                if i % 2 == 0:
                    ax.axvspan(k0 / 30.0, k1 / 30.0, color="#EFEFEF", lw=0, zorder=0)
            ax.set_xlim(0, 30)
        ax1.plot(t, s[:, 2] * 1000, color=col, lw=1.0)
        g = a[:, 9].astype(float)
        ax1b = ax1.twinx()
        ax1b.plot(t, g, color=S.G2, lw=0.7, ls=(0, (2, 1.2)))
        ax1b.set_ylim(-0.1, 3.5)
        ax1b.set_yticks([])
        ax1b.spines["right"].set_visible(False)
        ax1.set_ylabel("z (mm)")
        ax1.set_ylim(70, 300)
        ax1.set_yticks([100, 200])
        yw = yaw_of(s)
        ax2.plot(t, yw - yw[0], color=col, lw=1.0)
        ax2.set_ylim(-60, 60)
        ax2.set_ylabel(T("손목 회전 (°)", "wrist yaw (°)"))
        nj = s.shape[1] - 10
        q = s[:, 10:10 + nj].astype(float)
        dq = np.abs(np.gradient(q, 1 / 30.0, axis=0)) / lim[None, :nj]
        ax3.plot(t, dq.max(axis=1), color=col, lw=0.9)
        ax3.axhline(1.0, color=S.G1, ls=(0, (3, 2)), lw=0.7)
        ax3.set_ylim(0, 1.15)
        ax3.set_ylabel(T("최대 비", "max ratio"))
        ax1.text(0.02, 0.92, ("FR3" if rb == "fr3" else "FR5") + " · %.1f s" % (len(s) / 30.0), transform=ax1.transAxes, fontsize=6.3, color=col, va="top", fontweight="bold")
        if row == 0:
            for ax in (ax1, ax2, ax3):
                plt.setp(ax.get_xticklabels(), visible=False)
            ax1.set_title(T("손끝 높이", "TCP height"), fontsize=7)
            ax2.set_title(T("손목 회전 (시작 대비)", "wrist yaw (rel. start)"), fontsize=7)
            ax3.set_title(T("관절 속도 / 한계", "joint speed / limit"), fontsize=7)
            S.panel(ax1, "b")
            S.panel(ax2, "c")
            S.panel(ax3, "d")
        else:
            for ax in (ax1, ax2, ax3):
                ax.set_xlabel(T("시간 (s)", "time (s)"))
    S.save(fig, "fig_traj")
    return p


# ------------------------------------------------------------------ 구간 시간
def fig_stages():
    fig, ax = plt.subplots(figsize=(S.COL1, 1.55))
    rows = [("AB100", "fr3"), ("AB100", "fr5"), ("ab_A", "fr3"), ("ab_A", "fr5")]
    shades = ["#2B2B2B", "#5A5A5A", "#808080", "#A3A3A3", "#C2C2C2", "#DADADA", "#EDEDED"]
    for i, (d, rb) in enumerate(rows):
        x = ST["auto"][d][rb]["stage_s"]
        left = 0
        for j, (k, _, _) in enumerate(ST_ORDER):
            v = x[k]["p50"] if x.get(k) else 0
            ax.barh(i, v, left=left, color=shades[j], height=0.62, edgecolor="white", lw=0.5)
            left += v
        tot = ST["auto"][d][rb]["seconds"]["p50"]
        ax.text(left + 0.6, i, "%.1f s" % tot, va="center", fontsize=6.2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["%s %s" % ("FR3" if rb == "fr3" else "FR5", DSL[d]) for d, rb in rows])
    for t, (d, rb) in zip(ax.get_yticklabels(), rows):
        t.set_color(S.ROBOT_C[rb])
    ax.invert_yaxis()
    ax.set_xlim(0, 44)
    ax.set_xlabel(T("구간 시간 중앙값 (s)", "median phase duration (s)"))
    h = [Rectangle((0, 0), 1, 1, color=c, ec="white") for c in shades]
    ax.legend(h, [stname(k) for k, _, _ in ST_ORDER], loc="upper center", bbox_to_anchor=(0.45, 1.33), ncol=4, fontsize=5.8, handlelength=0.9, columnspacing=0.7, handletextpad=0.3)
    S.save(fig, "fig_stages")


# ------------------------------------------------------------------ 학습 손실
def fig_train():
    runs = [("fr3_100ep_20261103_1604", "fr3", (0, (3, 1.5)), T("AB 100 · 30 Hz", "AB 100 · 30 Hz")),
            ("fr3_100ep_real10hz_20261108_2244", "fr3", "-", "ab n100 · 10 Hz"),
            ("fr3_200ep_real10hz_20261109_0114", "fr3", (0, (1, 1)), "ab n200 · 10 Hz"),
            ("fr5_100ep_20261103_1604", "fr5", (0, (3, 1.5)), T("AB 100 · 30 Hz", "AB 100 · 30 Hz")),
            ("fr5_100ep_real10hz_20261108_2244", "fr5", "-", "ab n100 · 10 Hz"),
            ("fr5_200ep_real10hz_20261109_0046", "fr5", (0, (1, 1)), "ab n200 · 10 Hz")]
    fig, axs = plt.subplots(1, 2, figsize=(S.COL1, 1.6), sharey=True)
    for ax, rb in zip(axs, ("fr3", "fr5")):
        for name, r, ls, lab in runs:
            if r != rb or name not in ST["train"]:
                continue
            x = ST["train"][name]
            st, lo = np.array(x["steps"]), np.array(x["loss"])
            k = 25
            sm = np.convolve(lo, np.ones(k) / k, mode="valid")
            ax.plot(st[k - 1:] / 1000.0, sm, color=S.ROBOT_C[rb], ls=ls, lw=0.9, label=lab)
        ax.set_yscale("log")
        ax.set_xlabel(T("스텝 (천)", "step (k)"))
        ax.set_title("FR3" if rb == "fr3" else "FR5", fontsize=7, color=S.ROBOT_C[rb])
        ax.set_xlim(0, 20)
        ax.legend(fontsize=5.4, loc="upper right", handlelength=1.8, borderaxespad=0.1)
    axs[0].set_ylabel(T("학습 손실 (이동 평균)", "training loss (moving avg.)"))
    fig.subplots_adjust(wspace=0.12)
    S.save(fig, "fig_train")


# ------------------------------------------------------------------ 벤치
def fig_bench_res():
    B = ST["bench"]
    rows = [("fr3_AB100_30hz_A", "fr3", T("AB 100, 30 Hz", "AB 100, 30 Hz"), "A"),
            ("fr5_AB100_30hz_A", "fr5", T("AB 100, 30 Hz", "AB 100, 30 Hz"), "A"),
            ("fr5_ab11_n100_C", "fr5", "ab n100, 10 Hz", "C"),
            ("fr5_ab11_n200_C", "fr5", "ab n200, 10 Hz", "C"),
            ("fr3_ab11_n100_C", "fr3", "ab n100, 10 Hz", "C"),
            ("fr3_ab11_n200_C", "fr3", "ab n200, 10 Hz", "C")]
    rows = [r for r in rows if B.get(r[0])]
    fig, axs = plt.subplots(1, 2, figsize=(S.COL1, 1.85), gridspec_kw={"width_ratios": [1.0, 1.15]})
    ax = axs[0]
    for i, (k, rb, lab, lay) in enumerate(rows):
        x = B[k]
        p, (lo, hi) = 100 * x["rate"], x["ci"]
        ax.errorbar(p, i, xerr=[[max(0, p - 100 * lo)], [max(0, 100 * hi - p)]], fmt="o", ms=3.4, color=S.ROBOT_C[rb], elinewidth=0.9, capsize=1.6, mew=0)
        ax.text(100 * hi + 2.5, i, "%d/%d" % (x["k"], x["n"]) + ("" if x["n"] >= 50 else "*"), va="center", fontsize=5.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["%s · %s" % (lab, lay) for _, _, lab, lay in rows], fontsize=6.0)
    for t, r in zip(ax.get_yticklabels(), rows):
        t.set_color(S.ROBOT_C[r[1]])
    ax.invert_yaxis()
    ax.set_xlim(0, 75)
    ax.set_xlabel(T("성공률 (%) · 95% 범위", "success (%) · 95% CI"))
    S.panel(ax, "a")
    ax = axs[1]
    stg = ["grasp", "lift", "over_slot", "success"]
    xl = [T("쥠", "grasp"), T("들어\n올림", "lift"), T("슬롯\n위", "over\nslot"), T("성공", "success")]
    for k, rb, lab, lay in rows:
        x = B[k]
        v = [100.0 * x["stages"][s] / max(1, x["n_rows"]) for s in stg]      # 튀지 않은 첫 판 가운데
        ls = "-" if lay == "C" else (0, (3, 1.5))
        mk = "o" if "n200" not in k else "s"
        ax.plot(range(4), v, color=S.ROBOT_C[rb], ls=ls, marker=mk, ms=2.8, lw=0.9, mew=0)
    ax.set_xticks(range(4))
    ax.set_xticklabels(xl, fontsize=6.0)
    ax.set_ylim(0, 105)
    ax.set_ylabel(T("단계에 이른 첫 판 (%)", "first trials reaching stage (%)"))
    ax.legend([Line2D([], [], color=S.G1, ls=(0, (3, 1.5))), Line2D([], [], color=S.G1, ls="-"), Line2D([], [], color=S.G1, marker="o", ls="", ms=3), Line2D([], [], color=S.G1, marker="s", ls="", ms=3)],
              [T("배치 A", "layout A"), T("배치 C", "layout C"), "n100", "n200"], fontsize=5.6, loc="upper right", ncol=2, handlelength=1.6, columnspacing=0.6, borderaxespad=0.1)
    S.panel(ax, "b")
    fig.subplots_adjust(wspace=0.5)
    S.save(fig, "fig_bench_res")


# ------------------------------------------------------------------ 실물 비교
REAL = {"fr3": {"z_close": 109.6, "yaw_state": (-26, 15), "yaw_close": (-27, 17), "x_close": (463, 664), "turn": 23, "tilt_med": 2.4},
        "fr5": {"z_close": 131.0}}
TOOL_SHIFT = {"fr3": -(103.4 - 97.0), "fr5": +(171.2 - 167.6)}      # 시뮬 TCP → 실물 공구 기준점 (손이 수직일 때 z 차)


def fig_real():
    fig, axs = plt.subplots(1, 3, figsize=(S.COL2, 1.8), gridspec_kw={"width_ratios": [1.15, 1.0, 1.0]})
    ax = axs[0]
    bins = np.arange(75, 140, 1.0)
    for rb, yy in (("fr3", 0.74), ("fr5", 0.9)):
        z = np.array(ST["traj"][rb + "_ab"]["z_close_raw"]) + TOOL_SHIFT[rb]
        ax.hist(z, bins=bins, color=S.ROBOT_C[rb], alpha=0.85, histtype="stepfilled", lw=0)
        zr = REAL[rb]["z_close"]
        ax.axvline(zr, color=S.ROBOT_C[rb], lw=1.4, ls=(0, (3, 1.5)))
        ax.annotate("", xy=(zr, yy), xytext=(np.median(z), yy), xycoords=("data", "axes fraction"),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color=S.ROBOT_C[rb]))
        ax.text((zr + np.median(z)) / 2, yy + 0.025, "+%.1f mm" % (zr - np.median(z)), transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=6.0, color=S.ROBOT_C[rb],
                bbox=dict(fc="white", ec="none", pad=0.3))
    ax.set_xlabel(T("닫을 때 손끝 z (mm, 실물 공구 기준점)", "TCP z at close (mm, real tool point)"))
    ax.set_ylabel(T("시연 수", "demos"))
    ax.legend([Rectangle((0, 0), 1, 1, color=S.C3), Rectangle((0, 0), 1, 1, color=S.C5), Line2D([], [], color=S.G1, ls=(0, (3, 1.5)))],
              [T("FR3 시뮬", "FR3 sim"), T("FR5 시뮬", "FR5 sim"), T("실물 중앙값", "real median")], fontsize=5.8, loc="center right", bbox_to_anchor=(1.03, 0.45), borderaxespad=0.1, handlelength=1.2)
    ax.set_xlim(75, 170)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
    S.panel(ax, "a")
    # (b) FR3 yaw 분포
    ax = axs[1]
    yc = np.array(ST["traj"]["fr3_ab"]["yaw_close_raw"])
    ax.hist(yc, bins=np.arange(-180, 181, 7.5), color=S.C3, histtype="stepfilled", lw=0, alpha=0.85)
    yl = ax.get_ylim()[1]
    lo, hi = np.percentile(yc, [5, 95])
    ax.plot([lo, hi], [yl * 1.08] * 2, color=S.C3, lw=2.2, solid_capstyle="butt")
    ax.plot(REAL["fr3"]["yaw_close"], [yl * 1.2] * 2, color=S.G1, lw=2.2, solid_capstyle="butt")
    ax.text(hi + 6, yl * 1.08, T("시뮬 5–95%", "sim 5–95%"), va="center", fontsize=5.8, color=S.C3)
    ax.text(REAL["fr3"]["yaw_close"][1] + 6, yl * 1.2, T("실물 5–95%", "real 5–95%"), va="center", fontsize=5.8)
    ax.set_ylim(0, yl * 1.3)
    ax.set_xlim(-180, 180)
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_xlabel(T("FR3 닫을 때 손목 yaw (°)", "FR3 wrist yaw at close (°)"))
    ax.set_ylabel(T("시연 수", "demos"))
    S.panel(ax, "b")
    # (c) FR3 닫는 자리 x
    ax = axs[2]
    xc = np.array(ST["traj"]["fr3_ab"].get("x_close_raw") or [])
    ax.hist(xc, bins=np.arange(250, 700, 12.5), color=S.C3, histtype="stepfilled", lw=0, alpha=0.85)
    yl = ax.get_ylim()[1]
    ax.plot(REAL["fr3"]["x_close"], [yl * 1.1] * 2, color=S.G1, lw=2.2, solid_capstyle="butt")
    ax.plot([xc.min(), xc.max()], [yl * 1.22] * 2, color=S.C3, lw=2.2, solid_capstyle="butt")
    ax.text(REAL["fr3"]["x_close"][0], yl * 1.1 - yl * 0.06, T("실물 범위", "real range"), va="top", fontsize=5.8)
    ax.text(xc.max() + 8, yl * 1.22, T("시뮬 범위", "sim range"), va="center", fontsize=5.8, color=S.C3)
    ax.set_ylim(0, yl * 1.32)
    ax.set_xlim(250, 700)
    ax.set_xlabel(T("FR3 닫을 때 손끝 x (mm)", "FR3 TCP x at close (mm)"))
    ax.set_ylabel(T("시연 수", "demos"))
    S.panel(ax, "c")
    fig.subplots_adjust(wspace=0.55)
    S.save(fig, "fig_real")


# ------------------------------------------------------------------ 장면 사진 (실물 · 시뮬)
def fig_scene(root, with_real=True):
    from PIL import Image
    fr = os.path.join(EX, "frames")
    photos = os.path.join(os.path.dirname(os.path.abspath(SP)), "real_photos")
    rows = [("fr3", os.path.join(root, "ref_fr3", "third_real.png")), ("fr5", os.path.join(photos, "fr5_third_real_1110.png"))]
    cols = [(T("실물 3인칭", "real, third-person"), None), (T("시뮬 3인칭 · 시작", "sim third · start"), "third_start"),
            (T("시뮬 3인칭 · 끝", "sim third · end"), "third_end"), (T("시뮬 손목 · 쥔 뒤 (옮기는 중)", "sim wrist · after grasp (carry)"), "wrist_mid")]
    if not with_real:
        cols = cols[1:]
    fig, axs = plt.subplots(2, len(cols), figsize=(S.COL2 * len(cols) / 4.0, 2.02))
    for i, (rb, real) in enumerate(rows):
        for j, (lab, key) in enumerate(cols):
            ax = axs[i, j]
            p = real if key is None else os.path.join(fr, "%s_pair1103-5_%s.png" % (rb, key))
            if os.path.isfile(p):
                im = Image.open(p).convert("RGB")
                w, h = im.size
                tw = int(h * 16 / 9) if w / h > 16 / 9 + 0.01 else w
                th = int(w * 9 / 16) if w / h < 16 / 9 - 0.01 else h
                im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th))
                ax.imshow(im)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(True)
                sp.set_linewidth(0.4)
            if i == 0:
                ax.set_title(lab, fontsize=6.8, pad=2)
            if j == 0:
                ax.set_ylabel("FR3" if rb == "fr3" else "FR5", color=S.ROBOT_C[rb], fontsize=8, fontweight="bold")
    fig.subplots_adjust(wspace=0.03, hspace=0.05)
    S.save(fig, "fig_scene" if with_real else "fig_scene_sim")


if __name__ == "__main__":
    ROOT = os.environ.get("BIO_ROOT", "/home/claude/Medical_bio_experiment")
    todo = {"fig_mathmodel": fig_mathmodel, "fig_traj": fig_traj, "fig_stages": fig_stages, "fig_train": fig_train,
            "fig_bench_res": fig_bench_res, "fig_real": fig_real, "fig_scene": lambda: fig_scene(ROOT), "fig_scene_sim": lambda: fig_scene(ROOT, with_real=False)}
    for lang in ("ko", "en"):
        S.set_lang(lang)
        T = S.T
        for k, f in todo.items():
            if not ONLY or k in ONLY:
                r = f()
                if k == "fig_traj" and lang == "ko":
                    print("[traj] 짝", r)
