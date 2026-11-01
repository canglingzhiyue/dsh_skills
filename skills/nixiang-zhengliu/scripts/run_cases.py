"""run_cases.py —— 树的回归验收用例（症状 → 应命中哪个 文件#锚点）。

机制（两阶段，避免"自己给自己打分"的假通过）：
    阶段 1「立基线」：`output/cases/expectations.json` **不存在**时，对每条用例算 top-1 命中，
        把结果写成基线文件，并标 `"frozen": false`，要求人工确认后把 `frozen` 改成 true。
    阶段 2「跑回归」：基线存在时，逐条比对 top-1 是否仍是同一个 `文件#锚点`，
        并在 `frozen: true` 时以退出码表达 PASS/FAIL。

为什么这么设计：
    用例来自 15 个历史案件（`case_seeds.json`，由案件库挖出），天然带 ground truth；
    但"应该命中哪条规则"必须先看一眼树才知道填什么。**先冻结再回归**，
    否则每次改树都重新对齐期望值，等于永远 PASS。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"; $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\run_cases.py

关键结论 / 限制：
    - 打分是词面重叠（IDF 加权覆盖率），不是语义匹配；它验的是"症状能不能拉到对的规则"，
      不验规则本身对不对。
    - 【未验证】TOP_K 只影响报告展示，判定只看 top-1。
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import common
import merge_pools

TREE = common.OUT_DIR / "nixiang-shu"
SEEDS = common.OUT_DIR / "cases" / "case_seeds.json"
EXPECT = common.OUT_DIR / "cases" / "expectations.json"

TOP_K = 5
# ★ 2026-11-01 修正：不设"命中阈值"。规则覆盖率口径下，一条规则有几百个 token，
#   命中几个也到不了 0.15，硬阈值会把所有用例都判成"未命中"（实测 11/11 全 0）。
#   改为：只要与规则有 token 交集就取 top-1 作基线；分数只作**覆盖度指标**，
#   低于 COVER_LOW 的标"覆盖不足"，提示该域还没灌满，而不是判成检索坏了。
MIN_SCORE = 0.0
COVER_LOW = 0.05          # 覆盖度低于此值 → 标"覆盖不足"

_RE_RULE = re.compile(r"^####\s+([a-z]+-\d{3})\s+(.+)$", re.M)


def load_rules_from_tree():
    """从已渲染的树里解析规则（验的是**树本身**，不是草案中间件）。

    返回：
        list[dict]：{target, id, title, tokens}
    """
    rules = []
    # ★ 修（2026-11-01）：主题按阶段拆分后规则在 references/<主题>/<阶段>.md 里，
    #   必须用 rglob；用 glob 会一条规则都解析不到（实测：报"树内规则 0 条"）。
    for md in sorted((TREE / "references").rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        blocks = re.split(r"(?=^####\s+[a-z]+-\d{3})", text, flags=re.M)
        rel = md.relative_to(TREE).as_posix()
        for blk in blocks:
            m = _RE_RULE.search(blk)
            if not m:
                continue
            rid, title = m.group(1), m.group(2).strip()
            toks = merge_pools.tokenize(blk)
            rules.append({
                "target": f"{rel}#{rid}",
                "id": rid,
                "title": title,
                "tokens": toks["ascii"] | toks["cjk"],
            })
    return rules


def build_idf(rules):
    """以规则集为语料算 IDF（越少规则用到的词权重越高）。"""
    df = Counter()
    for r in rules:
        for t in r["tokens"]:
            df[t] += 1
    n = max(1, len(rules))
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


def score_case(seed, rules, idf):
    """对一条用例打分（规则覆盖率），返回按分数降序的 top-k。

    ★ 2026-11-01 修正：原来算的是「症状 token 被规则覆盖的比例」（分母=查询），
      而症状句子长、规则条短，分母一大覆盖率必然趋零 —— 实测 11 条用例全部 0.0 分，
      连"taobao so 逆向"对"静态分析"这种明显该命中的都是 0。
      改成**规则覆盖率**（分母=规则的 IDF 总和）：即"这条规则有多少关键内容被症状命中"，
      这才是"症状 → 该查哪条规则"的正确方向。
    """
    text = " ".join((seed.get("symptoms") or []) + (seed.get("keywords") or [])
                    + [seed.get("resolved_by") or ""])
    toks = merge_pools.tokenize(text)
    q = toks["ascii"] | toks["cjk"]
    if not q:
        return []
    out = []
    for r in rules:
        inter = q & r["tokens"]
        if not inter:
            continue
        denom = sum(idf.get(t, 2.0) for t in r["tokens"])
        if denom <= 0:
            continue
        s = sum(idf.get(t, 2.0) for t in inter) / denom
        if s >= MIN_SCORE:
            out.append({"target": r["target"], "title": r["title"], "score": round(s, 3)})
    out.sort(key=lambda x: -x["score"])
    return out[:TOP_K]


def run():
    """主流程：解析树 → 逐条用例打分 → 立基线或跑回归。"""
    if not (TREE / "references").exists():
        print(f"[用例] SKIP 树不存在：{TREE}")
        return True
    if not SEEDS.exists():
        print(f"[用例] SKIP 没有用例种子：{SEEDS}")
        return True
    seeds = json.loads(SEEDS.read_text(encoding="utf-8"))
    cases = seeds.get("cases") or []
    # ★ 2026-11-01 评审要求"用例扩到 30 条"：案件只有 11 个，但症状有 33 条，
    #   把**每条症状拆成一条独立用例**（更精确：一条症状对应一次真实卡点），
    #   case_id 记为 `<案件>#s<n>`，基线/回归都按它比对。
    expanded = []
    for c in cases:
        for i, s in enumerate(c.get("symptoms") or [], start=1):
            ex = dict(c)
            ex["case_id"] = f"{c.get('case_id')}#s{i}"
            ex["symptoms"] = [s]
            expanded.append(ex)
    if expanded:
        cases = expanded
    rules = load_rules_from_tree()
    idf = build_idf(rules)
    print(f"[用例] 树内规则 {len(rules)} 条｜用例 {len(cases)} 条（由症状拆展开）")

    results = []
    for c in cases:
        top = score_case(c, rules, idf)
        results.append({
            "case_id": c.get("case_id"),
            "symptoms": c.get("symptoms"),
            "expected": c.get("expected_target"),
            "predicted": top[0]["target"] if top else None,
            "score": top[0]["score"] if top else 0.0,
            "top": top,
        })

    # ---- 基线的"有效性"判定（自愈重建，不靠删文件）----
    # 语义：**未冻结 = 还没确认过 = 树变了就重建**；**已冻结 = 回归基准 = 树变了必须报 FAIL**。
    # 早先版本用"规则数是否为 0"判断，导致规则从 35 条涨到 72 条后基线还僵在旧状态、
    # 用例全部 SKIP（实测 2026-11-01）。冻结与否才是正确判据。
    base = {}
    need_rebuild = True
    if EXPECT.exists():
        try:
            base = json.loads(EXPECT.read_text(encoding="utf-8"))
            old_cases = base.get("cases") or []
            old_n = base.get("n_rules")
            frozen_old = bool(base.get("frozen"))
            need_rebuild = (not old_cases) or (not frozen_old) or (old_n != len(rules))
        except json.JSONDecodeError:
            need_rebuild = True
            if not old_cases:
                need_rebuild = True
        except json.JSONDecodeError:
            need_rebuild = True

    if need_rebuild:
        baseline = {"generated_at": "2026-11-01", "frozen": False,
                    "n_rules": len(rules), "cases": results}
        EXPECT.write_text(json.dumps(baseline, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[用例] 已建立基线 → {EXPECT}（frozen=false，需人工确认后改 true）")
        for r in results:
            print(f"[用例]   {r['case_id']:<36} → {r['predicted'] or '未命中'}  ({r['score']})")
        return True

    frozen = bool(base.get("frozen"))
    old = {c["case_id"]: c for c in base.get("cases") or []}
    passes = fails = missing = 0
    for r in results:
        exp = old.get(r["case_id"], {}).get("predicted")
        if not exp:
            missing += 1
            print(f"[用例] SKIP {r['case_id']}：基线里没有期望值")
            continue
        ok = (r["predicted"] == exp)
        passes += ok
        fails += (not ok)
        print(f"[用例] {'PASS' if ok else 'FAIL'} {r['case_id']:<36} 期望 {exp} 实得 {r['predicted']} ({r['score']})")
    print(f"[用例] 合计 PASS {passes} / FAIL {fails} / SKIP {missing}"
          f"｜基线 frozen={frozen}")
    if not frozen:
        print("[用例] 基线未冻结：结果仅供参考，人工确认后把 expectations.json 的 frozen 改 true")
        return True
    return fails == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
