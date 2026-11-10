"""analyze.py — 내보낸 기록 (paper_export_1110) 에서 원고 수치를 계산해 data/stats.json 으로.
    python3 -I analyze.py <paper_export_1110 경로> <출력 json>
읽기만 함. 모든 수치는 여기서 나오고, 원고 · 그림은 이 json 을 씀.
"""
import collections
import glob
import json
import math
import os
import sys

import numpy as np

EX = sys.argv[1]
OUTP = sys.argv[2]
TX = os.path.join(EX, "text")

AUTO = {   # 묶음 이름: (FR3 폴더, FR5 폴더)
    "AB100": ("fr3/005_20261102_pair100b_1103", "fr5/007_20261102_pair100b_1103"),
    "AB_A200": ("fr3/009_20261103_pair500_1104", "fr5/010_20261103_pair500_1104"),
    "AB_B": ("fr3/012_20261105_pairB_1105", "fr5/012_20261106_pairB_1105"),
    "ab_A": ("fr3/018_20261107_ab_a_1103", "fr5/016_20261107_ab_a_1103"),
    "ab_B": ("fr3/019_20261108_ab_b_1105", "fr5/017_20261108_ab_b_1105"),
}
FR3FAIL = ["fr5/008_20261103_fr3fail_1103", "fr5/013_20261107_fr3fail_1104", "fr5/014_20261107_fr3fail_1105"]
BENCH = {
    "fr3_AB100_30hz_A": "fr3/010_20261104_bench_fr3_ck20000",
    "fr3_AB100_30hz_seen": "fr3/011_20261105_bench_fr3_ck20000_seen",
    "fr5_AB100_30hz_A": "fr5/011_20261104_bench_fr5_ck20000",
    "fr5_ab11_n100_C": "fr5/019_20261110_bench_fr5_ab11_n100_C",
    "fr5_ab11_n200_C": "fr5/020_20261110_bench_fr5_ab11_n200_C",
}
for g in glob.glob(os.path.join(TX, "fr[35]", "*_bench_fr[35]_ab11_n[12]00_[ABC]")):     # 나중에 받는 벤치도 저절로
    k = os.path.basename(g).split("_bench_")[1].replace("ab11_", "ab11_")
    BENCH.setdefault(k, os.path.relpath(g, TX))


def jl(p):
    out = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except OSError:
        pass
    return out


def wilson(k, n, z=1.96):
    if n <= 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def q(a, ps=(5, 25, 50, 75, 95)):
    a = np.asarray([x for x in a if x is not None and np.isfinite(x)], float)
    if a.size == 0:
        return None
    return {"n": int(a.size), "mean": float(a.mean()), "min": float(a.min()), "max": float(a.max()),
            **{"p%d" % p: float(np.percentile(a, p)) for p in ps}}


def discard_kind(why):
    w = why or ""
    if "손에서 벗어남" in w:
        return "slip"
    if "빈 랙 구멍에 없음" in w or "구멍에 없음" in w:
        return "not_in_hole"
    if "덜 꽂힘" in w:
        return "shallow"
    if "기울" in w and "12" in w:
        return "tilt"
    if "움직임" in w:
        return "moving"
    return "other"


STAGES = [("approach", ["튜브로 가기"]), ("grasp", ["쥐기 전 멈춤", "쥐기", "쥔 채 기다림"]), ("carry", ["옮기기"]),
          ("align", ["구멍 위에서 멈춤", "구멍 맞추기"]), ("insert", ["꽂기 전 멈춤", "꽂기"]),
          ("release", ["놓기 전 멈춤", "놓기", "놓은 뒤 멈춤"]), ("retreat", ["위로 빠지기"])]
NAME2ST = {n: s for s, ns in STAGES for n in ns}


def auto_folder(rel):
    F = os.path.join(TX, rel)
    if not os.path.isdir(F):
        return None
    H = jl(os.path.join(F, "progress", "history.jsonl"))
    E = jl(os.path.join(F, "progress", "episodes.jsonl"))
    stops = collections.defaultdict(list)          # scene → [success, ...] 차례대로
    disc = collections.Counter()
    skip = collections.Counter()
    gave = 0
    ends = []
    first_fail = set()
    skipped = {}
    for e in H:
        ev = e.get("event")
        if ev == "stop":
            stops[e.get("scene")].append(bool(e.get("success")))
        elif ev == "auto_discard":
            disc[discard_kind(e.get("why"))] += 1
            gave += 1 if e.get("gave_up") else 0
            if int(e.get("attempt") or 0) == 0:
                first_fail.add(e.get("scene"))
        elif ev == "auto_skip":
            skipped.setdefault(e.get("scene"), (e.get("kind") or "other").replace("other_", "fr5_"))
        elif ev in ("auto_end", "auto_follow_end"):
            ends.append(e)
    skip = collections.Counter(skipped.values())
    nd = sum(disc.values())
    scenes = len(stops)
    first = scenes - len(first_fail & set(stops))
    sv = len(E)
    att = sv + nd
    # 저장된 시연
    dax, tilt, bot, yax, ring, secs, wall = [], [], [], [], [], [], []
    st = collections.defaultdict(list)
    stepms = collections.defaultdict(list)
    for r in E:
        s = r.get("success") or {}
        dax.append(s.get("red_axis_at_collar_mm"))
        tilt.append(s.get("red_tilt_deg"))
        bot.append(s.get("red_bottom_from_goal_mm"))
        yax.append(s.get("yellow_axis_at_collar_mm"))
        ring.append(s.get("ring_from_goal_mm"))
        secs.append(r.get("seconds"))
        wall.append(r.get("wall_seconds"))
        sm = s.get("step_ms") or {}
        for k, v in sm.items():
            if isinstance(v, (int, float)):
                stepms[k].append(v)
        tl = ((r.get("input_stats") or {}).get("auto") or {}).get("timeline") or []
        if tl:
            n = r.get("length") or 0
            dur = collections.Counter()
            for i, (name, k0) in enumerate(tl):
                k1 = tl[i + 1][1] if i + 1 < len(tl) else n
                if name in NAME2ST:
                    dur[NAME2ST[name]] += (k1 - k0) / 30.0
            for k, _ in STAGES:
                st[k].append(dur.get(k, 0.0))
    minutes = sum(float(e.get("minutes") or 0) for e in ends)
    return {
        "folder": rel, "scenes": scenes, "attempts": att, "saved_stops": sv, "episodes": len(E), "first_try": first,
        "first_rate": first / scenes if scenes else None, "first_ci": wilson(first, scenes),
        "per_attempt": sv / att if att else None, "discarded": nd, "per_attempt_ci": wilson(sv, att),
        "discard": dict(disc), "skip": dict(skip), "gave_up": gave,
        "minutes": minutes, "demos_per_hour": (len(E) / (minutes / 60.0)) if minutes else None,
        "sim_s_total": float(np.nansum([x for x in secs if x])),
        "d_ax": q(dax), "tilt": q(tilt), "bottom": q(bot), "yellow_ax": q(yax), "ring": q(ring), "seconds": q(secs),
        "stage_s": {k: q(v) for k, v in st.items()},
        "step_ms": {k: float(np.mean(v)) for k, v in stepms.items()},
        "dax_raw": [x for x in dax if x is not None], "tilt_raw": [x for x in tilt if x is not None],
        "sec_raw": [x for x in secs if x is not None],
        "stage_raw": {k: v for k, v in st.items()},
    }


def bench_folder(rel):
    F = os.path.join(TX, rel)
    R = jl(os.path.join(F, "progress", "bench_results.jsonl"))
    if not R:
        return None
    n = len(R)
    k = sum(1 for r in R if r.get("success"))
    stg = {s: sum(1 for r in R if (r.get("stages") or {}).get(s)) for s in ("grasp", "lift", "over_slot", "success")}
    ends = collections.Counter(r.get("end") or "?" for r in R)
    qn = [r.get("queries") for r in R if r.get("queries")]
    ms = [r.get("ms_mean") for r in R if r.get("ms_mean")]
    sms = [r.get("server_ms_mean") for r in R if r.get("server_ms_mean")]
    succ_s = [r.get("seconds") for r in R if r.get("success")]
    ikf = sum(r.get("ik_fail") or 0 for r in R)
    ikt = sum(r.get("ik_total") or 0 for r in R)
    model = R[0].get("model")
    return {"folder": rel, "n": n, "k": k, "rate": k / n, "ci": wilson(k, n), "stages": stg, "end": dict(ends),
            "queries": q(qn), "ms_mean": q(ms), "server_ms": q(sms), "success_s": q(succ_s), "ik_fail_rate": (ikf / ikt) if ikt else None,
            "model": os.path.basename(os.path.dirname(model)) if model else None,
            "first_s": {s: q([(r.get("first_s") or {}).get(s) for r in R]) for s in ("grasp", "lift", "over_slot")},
            "rows": [{"scene": r.get("scene"), "success": bool(r.get("success")), "stages": r.get("stages"), "end": r.get("end"),
                      "seconds": r.get("seconds"), "min_hole_mm_lifted": r.get("min_hole_mm_lifted"), "max_lift_mm": r.get("max_lift_mm")} for r in R]}


def traj_stats(files):
    yaw_all, yaw_close, z_close, z_rel, x_close, turn = [], [], [], [], [], []
    for f in files:
        p = os.path.join(EX, "traj", f)
        if not os.path.isfile(p):
            continue
        z = np.load(p)
        lens, s, xyz, g, axyz = z["lens"], z["s_rest"].astype(np.float64), z["s_xyz"].astype(np.float64), z["a_g"][:, 0].astype(float), z["a_xyz"].astype(np.float64)
        o = 0
        for L in lens:
            r = s[o:o + L]
            yaw = np.degrees(np.arctan2(r[:, 3], r[:, 0]))
            yaw_all.append(yaw)
            yu = np.degrees(np.unwrap(np.radians(yaw)))
            turn.append(float(yu.max() - yu.min()))
            gg = g[o:o + L]
            if (gg > 0.5).any():
                k = int(np.argmax(gg > 0.5))
                yaw_close.append(float(yaw[k]))
                z_close.append(float(xyz[o + k, 2]))
                x_close.append(float(xyz[o + k, 0]))
                kr = k + int(np.argmax(gg[k:] < 0.5)) if (gg[k:] < 0.5).any() else None
                if kr is not None:
                    z_rel.append(float(xyz[o + kr, 2]))
            o += L
    ya = np.concatenate(yaw_all) if yaw_all else np.array([])
    return {"yaw_state": q(ya), "yaw_close": q(yaw_close), "z_close_mm": q(np.array(z_close) * 1000), "z_release_mm": q(np.array(z_rel) * 1000),
            "x_close_mm": q(np.array(x_close) * 1000), "turn_deg": q(turn), "yaw_gt90": int(sum(1 for y in yaw_all if np.abs(y).max() > 90)), "n_ep": len(yaw_all),
            "yaw_close_raw": yaw_close, "z_close_raw": list(np.array(z_close) * 1000), "turn_raw": turn, "x_close_raw": list(np.array(x_close) * 1000)}


def train_runs():
    out = {}
    for d in sorted(glob.glob(os.path.join(EX, "..", "..", "sch", "tsk", "groot", "runs", "*"))):
        name = os.path.basename(d)
        ts = sorted(glob.glob(os.path.join(d, "checkpoint-*", "trainer_state.json")), key=lambda p: int(p.split("checkpoint-")[1].split("/")[0]))
        if not ts:
            continue
        t = json.load(open(ts[-1]))
        lh = [x for x in t.get("log_history", []) if "loss" in x]
        info = {}
        ri = os.path.join(d, "run_info.txt")
        if os.path.isfile(ri):
            for line in open(ri, encoding="utf-8", errors="replace"):
                if line[:13].strip() and len(line) > 13:
                    info[line[:13].strip()] = line[13:].strip()
        steps = [x["step"] for x in lh]
        loss = [x["loss"] for x in lh]
        last = float(np.mean(loss[-50:])) if loss else None
        out[name] = {"steps": steps, "loss": loss, "last_mean_500": last, "max_step": t.get("global_step"), "dataset": info.get("dataset"), "episodes": info.get("episodes"),
                     "train_batch_size": t.get("train_batch_size")}
    return out


S = {"auto": {}, "fr3fail": {}, "bench": {}, "traj": {}, "train": {}}
for k, (a, b) in AUTO.items():
    S["auto"][k] = {"fr3": auto_folder(a), "fr5": auto_folder(b)}
for rel in FR3FAIL:
    S["fr3fail"][rel] = auto_folder(rel)
for k, rel in BENCH.items():
    S["bench"][k] = bench_folder(rel)
S["traj"]["fr3_ab"] = traj_stats(["fr3__018_20261107_ab_a_1103.npz", "fr3__019_20261108_ab_b_1105.npz"])
S["traj"]["fr5_ab"] = traj_stats(["fr5__016_20261107_ab_a_1103.npz", "fr5__017_20261108_ab_b_1105.npz"])
S["traj"]["fr3_AB100"] = traj_stats(["fr3__005_20261102_pair100b_1103.npz"])
S["traj"]["fr5_AB100"] = traj_stats(["fr5__007_20261102_pair100b_1103.npz"])
S["train"] = train_runs()
real = os.path.join(EX, "..", "..", "real", "share_fr3_meta_1110", "dataset_meta")
if os.path.isdir(real):
    S["real_fr3"] = {"info": {k: v for k, v in json.load(open(os.path.join(real, "info.json"))).items() if k in ("fps", "total_episodes", "total_frames", "codebase_version", "robot_type")},
                     "state": json.load(open(os.path.join(real, "stats.json")))["observation.state"],
                     "action": json.load(open(os.path.join(real, "stats.json")))["action"]}
json.dump(S, open(OUTP, "w"), ensure_ascii=False, indent=1, default=float)

# 요약 출력
for k, v in S["auto"].items():
    for rb in ("fr3", "fr5"):
        x = v[rb]
        if not x:
            print("%-8s %s 없음" % (k, rb))
            continue
        print("%-8s %s 장면 %3d 시도 %3d 저장 %3d (ep %3d) 첫 %3d (%.1f%%) 시도당 %.1f%% 버림 %s 건너뜀 %s 포기 %d · %.0f분 %.1f개/h · dax 중앙 %.2f p95 %.2f · 기울기 중앙 %.2f · 길이 중앙 %.1f s"
              % (k, rb, x["scenes"], x["attempts"], x["saved_stops"], x["episodes"], x["first_try"], 100 * (x["first_rate"] or 0), 100 * (x["per_attempt"] or 0),
                 x["discard"], x["skip"], x["gave_up"], x["minutes"], x["demos_per_hour"] or 0, x["d_ax"]["p50"], x["d_ax"]["p95"], x["tilt"]["p50"], x["seconds"]["p50"]))
for rel, x in S["fr3fail"].items():
    if x:
        print("fr3fail %s 장면 %d 시도 %d 저장 %d 첫 %d 버림 %s 건너뜀 %s" % (rel, x["scenes"], x["attempts"], x["saved_stops"], x["first_try"], x["discard"], x["skip"]))
for k, x in S["bench"].items():
    if x:
        print("bench %-22s %2d/%2d (%.0f%%, %.1f–%.1f) 단계 %s 끝 %s 물음 %.0f ms %.0f 서버 %.0f · %s" % (k, x["k"], x["n"], 100 * x["rate"], 100 * x["ci"][0], 100 * x["ci"][1], x["stages"], x["end"],
              x["queries"]["p50"] if x["queries"] else -1, x["ms_mean"]["p50"] if x["ms_mean"] else -1, x["server_ms"]["p50"] if x["server_ms"] else -1, x["model"]))
for k, x in S["traj"].items():
    print("traj %-10s yaw5-95 %.1f..%.1f close %.1f..%.1f z_close p50 %.1f rel p50 %s x_close %.0f..%.0f turn p50 %.1f |yaw|>90 %d/%d" % (
        k, x["yaw_state"]["p5"], x["yaw_state"]["p95"], x["yaw_close"]["p5"], x["yaw_close"]["p95"], x["z_close_mm"]["p50"],
        "%.1f" % x["z_release_mm"]["p50"] if x["z_release_mm"] else "-", x["x_close_mm"]["min"], x["x_close_mm"]["max"], x["turn_deg"]["p50"], x["yaw_gt90"], x["n_ep"]))
for k, x in S["train"].items():
    print("train %-34s %s 스텝 %s 마지막 손실(500) %.4f · %s" % (k, x["episodes"], x["max_step"], x["last_mean_500"] or -1, os.path.basename(x["dataset"] or "")))
