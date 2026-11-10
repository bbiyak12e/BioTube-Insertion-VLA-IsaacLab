"""matched.py — FR3 · FR5 를 같은 (장면, 시도) 목록에서 견줌. 시도의 결과: 버림 = 실패, 건너뜀 = 계획 못 함, 그 밖에 실행된 시도 = 저장.
    python3 -I matched.py <paper_export/text> [--json out.json]
"""
import collections, glob, json, os, sys
TX = sys.argv[1] if __name__ == "__main__" else None      # 가져다 쓸 때는 matched.TX = <text 폴더>
SETS = {"AB100": ("fr3/005_20261102_pair100b_1103", "fr5/007_20261102_pair100b_1103", ["fr5/008_20261103_fr3fail_1103"]),
        "AB_A200": ("fr3/009_20261103_pair500_1104", "fr5/010_20261103_pair500_1104", ["fr5/013_20261107_fr3fail_1104"]),
        "AB_B": ("fr3/012_20261105_pairB_1105", "fr5/012_20261106_pairB_1105", ["fr5/014_20261107_fr3fail_1105"]),
        "ab_A": ("fr3/018_20261107_ab_a_1103", "fr5/016_20261107_ab_a_1103", ["fr5/*fr3fail_ab_a*"]),
        "ab_B": ("fr3/019_20261108_ab_b_1105", "fr5/017_20261108_ab_b_1105", ["fr5/*fr3fail_ab_b*"])}


def outcomes(rel):
    out = {}
    for p in glob.glob(os.path.join(TX, rel)):
        plans = collections.defaultdict(list); disc = set(); skip = set(); stops = collections.Counter()
        for l in open(os.path.join(p, "progress", "history.jsonl"), encoding="utf-8"):
            if not l.strip():
                continue
            e = json.loads(l); t = e["event"]
            if t == "auto_plan": plans[e["scene"]].append(int(e.get("attempt") or 0))
            elif t == "auto_discard": disc.add((e["scene"], int(e.get("attempt") or 0)))
            elif t == "auto_skip": skip.add((e["scene"], int(e.get("attempt") or 0)))
            elif t == "stop": stops[e["scene"]] += 1
        for sc, a in skip:                      # 계획 단계에서 건너뜀 (auto_plan 없이 auto_skip 만 남음)
            out.setdefault((sc, a), None)
        for sc, al in plans.items():
            for i, a in enumerate(al):
                if (sc, a) in skip: out[(sc, a)] = None
                elif (sc, a) in disc: out[(sc, a)] = False
                elif i < stops[sc]: out[(sc, a)] = True
    return out


def discard_kind(why):
    """analyze.py 의 discard_kind 와 같음 (analyze.py 는 가져오면 바로 돌아서 따로 둠)."""
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


def reasons(rel):
    """(장면, 시도) → 버린 까닭 (analyze.discard_kind 와 같은 나눔: slip · not_in_hole · shallow · tilt · moving · other)."""
    out = {}
    for p in glob.glob(os.path.join(TX, rel)):
        for l in open(os.path.join(p, "progress", "history.jsonl"), encoding="utf-8"):
            if l.strip():
                e = json.loads(l)
                if e["event"] == "auto_discard":
                    out[(e["scene"], int(e.get("attempt") or 0))] = discard_kind(e.get("why"))
    return out


def main():
    R = {}
    for k, (f3, f5, ff) in SETS.items():
        a3 = {s: v for s, v in outcomes(f3).items() if v is not None}
        a5 = outcomes(f5)
        for f in ff: a5.update(outcomes(f))
        both = sorted(s for s in a3 if a5.get(s) is not None)
        nop5 = sorted(s for s in a3 if s in a5 and a5[s] is None)
        miss = sorted(s for s in a3 if s not in a5)
        first = [s for s in both if s[1] == 0]
        c = lambda L, d: sum(1 for s in L if d[s])
        R[k] = {"same_attempts": len(both), "fr3_ok": c(both, a3), "fr5_ok": c(both, a5), "first_scenes": len(first), "fr3_first_ok": c(first, a3), "fr5_first_ok": c(first, a5),
                "fr3_fail_in_same": sum(1 for s in both if not a3[s]), "fr5_ok_on_fr3_fail": sum(1 for s in both if not a3[s] and a5[s]),
                "fr5_fail_on_fr3_ok": sum(1 for s in both if a3[s] and not a5[s]), "fr5_cannot_plan": len(nop5), "missing": miss, "missing_first": [s for s in miss if s[1] == 0]}
        x = R[k]
        print("%-8s 같은 시도 %3d: FR3 %3d (%.1f%%) · FR5 %3d (%.1f%%) | 첫 시도 같은 장면 %3d: FR3 %3d · FR5 %3d | FR3 실패 %d → FR5 성공 %d | FR3 성공 → FR5 실패 %d | FR5 계획 못 함 %d | FR5 가 아직 안 한 시도 %d (첫 시도 %d)" % (
            k, x["same_attempts"], x["fr3_ok"], 100 * x["fr3_ok"] / x["same_attempts"], x["fr5_ok"], 100 * x["fr5_ok"] / x["same_attempts"], x["first_scenes"], x["fr3_first_ok"], x["fr5_first_ok"],
            x["fr3_fail_in_same"], x["fr5_ok_on_fr3_fail"], x["fr5_fail_on_fr3_ok"], x["fr5_cannot_plan"], len(miss), len(x["missing_first"])))
    if "--json" in sys.argv:
        json.dump(R, open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
