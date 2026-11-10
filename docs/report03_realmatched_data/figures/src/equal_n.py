"""equal_n.py — 표 3-1 · 그림 mathmodel 의 「같은 장면 · 같은 판 수」 비교 (2026-11-10).
    python3 -I equal_n.py <paper_export/text> <out.json>

같은 장면 n = 그 묶음에서 FR3 가 첫 시도 (attempt 0) 를 실제로 한 장면. FR5 는 같은 장면 · 같은 무작위 값의 첫 시도 결과
(FR5 짝 수집 + FR3 실패 다시 하기 폴더). FR5 가 계획을 못 한 것은 실패로 셈. 두 로봇 모두 계획 단계에서 빠진 장면은 n 에 없음 —
까닭이 FR3 (느림 · 틈) 인지 FR5 (other_clear · other_reach = 짝 로봇이 못 함) 인지 따로 셈.
FR3 버림 (모든 시도) 은 같은 (장면, 시도) 를 FR5 에 시킨 결과로 따로 셈.
"""
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matched as M  # noqa: E402

M.TX = TX = sys.argv[1]
OUT = sys.argv[2]
GROUPS = (("AB", ["AB100", "AB_A200", "AB_B"]), ("ab", ["ab_A", "ab_B"]))


def wil(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def excl(f3):
    sk, plans = collections.defaultdict(list), set()
    for l in open(os.path.join(TX, f3, "progress", "history.jsonl"), encoding="utf-8"):
        if not l.strip():
            continue
        e = json.loads(l)
        if e["event"] == "auto_skip":
            sk[e["scene"]].append(e.get("kind") or "")
        if e["event"] == "auto_plan":
            plans.add(e["scene"])
    c = collections.Counter()
    for s, ks in sk.items():
        if s not in plans:
            c["FR5" if all(k.startswith("other") for k in ks) else "FR3"] += 1
    return c


R = {}
for k, (f3, f5, ff) in M.SETS.items():
    a3, a5 = M.outcomes(f3), M.outcomes(f5)
    r3, r5 = M.reasons(f3), M.reasons(f5)
    for f in ff:
        a5.update(M.outcomes(f))
        r5.update(M.reasons(f))
    S = sorted(s for s in a3 if s[1] == 0 and a3[s] is not None)
    n = len(S)
    o3 = sum(1 for s in S if a3[s])
    r = [a5.get(s, "miss") for s in S]
    o5 = r.count(True)
    D = [s for s in a3 if a3[s] is False]
    rd = [a5.get(s, "miss") for s in D]
    both = [s for s in a3 if a3[s] is not None and a5.get(s) is not None]
    x = excl(f3)
    why3 = collections.Counter(r3.get(s, "other") for s in S if a3[s] is False)
    why5 = collections.Counter(r5.get(s, "other") for s in S if a5.get(s) is False)
    R[k] = dict(n=n, fr3=o3, fr3_ci=wil(o3, n), fr5=o5, fr5_ci=wil(o5, n), fr5_fail=r.count(False), fr5_noplan=r.count(None), notrun=r.count("miss"),
                fr3_disc=len(D), disc_fr5_ok=rd.count(True), disc_fr5_fail=rd.count(False), disc_fr5_noplan=rd.count(None), disc_notrun=rd.count("miss"),
                fr3ok_fr5fail=sum(1 for s in both if a3[s] and not a5[s]), excl_fr3=x["FR3"], excl_fr5=x["FR5"],
                fr3_first_why=dict(why3), fr5_first_why=dict(why5))
TOT = {}
for g, keys in GROUPS + (("all", [k for _, ks in GROUPS for k in ks]),):
    t = {f: sum(R[k][f] for k in keys) for f in ("n", "fr3", "fr5", "fr5_fail", "fr5_noplan", "notrun", "fr3_disc", "disc_fr5_ok", "disc_fr5_fail", "disc_fr5_noplan",
                                                   "disc_notrun", "fr3ok_fr5fail", "excl_fr3", "excl_fr5")}
    t["fr3_ci"], t["fr5_ci"] = wil(t["fr3"], t["n"]), wil(t["fr5"], t["n"])
    for w in ("fr3_first_why", "fr5_first_why"):
        c = collections.Counter()
        for k in keys:
            c.update(R[k][w])
        t[w] = dict(c)
    TOT[g] = t
json.dump({"sets": R, "groups": TOT, "rule": "same scenes = FR3 attempt-0 scenes; FR5 attempt 0 on the same scene and random draws; FR5 cannot-plan = failure"},
          open(OUT, "w"), ensure_ascii=False, indent=1)
for k, o in list(R.items()) + list(TOT.items()):
    print("%-8s n=%4d FR3 %4d (%.1f%%, %s) FR5 %4d (%.1f%%, %s) [실패 %d · 계획 못 함 %d · 안 함 %d] | FR3 버림 %d → FR5 저장 %d 실패 %d 계획 못 함 %d 안 함 %d | FR3 성공→FR5 실패 %d | 제외 FR3 %d FR5 %d | FR3 첫 실패 까닭 %s · FR5 %s" % (
        k, o["n"], o["fr3"], 100 * o["fr3"] / o["n"], o["fr3_ci"], o["fr5"], 100 * o["fr5"] / o["n"], o["fr5_ci"], o["fr5_fail"], o["fr5_noplan"], o["notrun"],
        o["fr3_disc"], o["disc_fr5_ok"], o["disc_fr5_fail"], o["disc_fr5_noplan"], o["disc_notrun"], o["fr3ok_fr5fail"], o["excl_fr3"], o["excl_fr5"], o["fr3_first_why"], o["fr5_first_why"]))
