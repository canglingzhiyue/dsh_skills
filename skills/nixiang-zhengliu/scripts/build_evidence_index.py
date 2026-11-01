"""build_evidence_index.py —— 规则级证据计数（把「跨库同簇=强共识」落到实处）。

为什么需要它（实测 2026-11-01）：
    句级跨平台聚类召回 ≈ 0（probe_similarity.py：字符三元组跨库最高分 0.02–0.12；
    ASCII 指纹用单个通用词就能给 1.000）。两库的人不会用同一句话讲同一件事。
    所以"一条规则有多少独立来源支持"只能在**规则级**上算：
    拿规则自己的关键词签名，回检索 35,532 条经验点，数独立 tid 与平台。

做什么：
    1. 读 `output/drafts/*.rules.json`（格式见 rule-schema.md）；
    2. 每条规则 → 查询 token 集（title + judge + action + keys），IDF 加权；
    3. 对全库经验点算「查询覆盖率」并取命中集；
    4. 统计独立来源 tid 数、平台数、年份跨度 → 定证据等级；
    5. 叠加图片/正文缺口的**证据上限**（口径见 plan.md §三）；
    6. 校验 anchors 是否真实存在（悬空锚点检查）；
    7. 输出 `output/drafts/<主题>.evidence.json` + 人读表格 `output/drafts/<主题>.证据表.md`。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"; $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\build_evidence_index.py

关键结论 / 限制：
    - 这是**检索式证据计数**，不是语义理解：命中≠同一条规则，只代表"讲的是同一件事"。
      所以 hit 数只用来定等级与找锚点候选，**规则正文仍以人/手册提炼为准**。
    - 【未验证】HIT_MIN=0.25 与 TOP_N=300 是首轮经验值，需用样板主题人工抽查后回调。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import common
import merge_pools

# ==== 调参旋钮 ====
HIT_MIN = 0.15          # 查询覆盖率阈值：规则 token 被该条经验点覆盖的比例
CORROBORATE_MIN = 0.35  # 视为"旁证"的最低分（只有它才影响等级，HIT_MIN 只影响线索列表）
TOP_N = 300             # 每条规则最多取多少条命中（够定级即可，不必全量）
KEYS_WEIGHT = 3.0       # keys 字段权重倍数（人工指定的技术指纹比散文词可靠得多）

DRAFT_GLOB = "*.rules.json"
IMG_INDEX = common.DATA_DIR / "img_index.json"


# ==== 载入 ====

def load_corpus():
    """载入两库经验点 + IDF 表，返回 (items, token_sets, idf)。

    复用 merge_pools 的载入与分词口径，保证与去重阶段一致。
    """
    items = merge_pools.load_52pj_items() + merge_pools.load_kanxue_items()
    token_sets, idf = merge_pools.build_idf(items)
    print(f"[证据] 语料 {len(items):,} 条，词表 {len(idf):,}")
    return items, token_sets, idf


def load_rules():
    """读全部规则草案草案文件，返回 [(path, doc)]。"""
    out = []
    for p in sorted((common.OUT_DIR / "drafts").glob(DRAFT_GLOB)):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[证据] ⚠ 跳过 {p.name}：{exc}")
            continue
        out.append((p, doc))
    return out


def load_img_index():
    """读图片/正文缺口索引（tid → evidence_cap）。"""
    if not IMG_INDEX.exists():
        print("[证据] ⚠ 未找到 img_index.json，跳过证据上限叠加")
        return {}
    return json.loads(IMG_INDEX.read_text(encoding="utf-8"))


# ==== 查询与打分 ====

def rule_query(rule):
    """把一条规则拼成查询 token 集。

    ★ 只用 keys + title + symptom，**不用 judge/action/if_not**（实测 2026-11-01）：
      把长散文拼进去会把查询稀释到 30+ 个 token，而池里的经验点是单句，
      覆盖率根本到不了阈值，命中数掉到 0–2，证据等级退化成"只看 declared 锚点"。
      keys 是人工挑的技术指纹，权重 KEYS_WEIGHT；标题与症状各 1.0。

    返回：
        (tokens, weights) —— tokens 是集合，weights 是 token → 权重
    """
    head = " ".join(str(rule.get(k) or "") for k in ("title",))
    head += " " + " ".join(rule.get("symptom") or [])
    keys = " ".join(rule.get("keys") or [])
    toks_head = merge_pools.tokenize(head)["ascii"] | merge_pools.tokenize(head)["cjk"]
    toks_keys = merge_pools.tokenize(keys)["ascii"] | merge_pools.tokenize(keys)["cjk"]
    weights = {}
    for t in toks_head:
        weights[t] = 1.0
    for t in toks_keys:
        weights[t] = max(weights.get(t, 0.0), KEYS_WEIGHT)
    return set(weights), weights


def score_item(q_tokens, q_weights, item_tokens, idf):
    """查询覆盖率：命中 token 的加权 IDF 和 / 查询 token 的加权 IDF 总和。

    参数：
        q_tokens / q_weights —— rule_query() 的输出
        item_tokens          —— 该经验点的 token 集
        idf                  —— token → IDF
    返回：
        float 0–1；无交集返回 0
    """
    inter = q_tokens & item_tokens
    if not inter:
        return 0.0
    denom = sum(q_weights[t] * idf.get(t, 1.0) for t in q_tokens)
    if denom <= 0:
        return 0.0
    num = sum(q_weights[t] * idf.get(t, 1.0) for t in inter)
    return num / denom


def retrieve(rule, items, token_sets, idf):
    """检索一条规则的支撑经验点。

    返回：
        list[dict]：按分数降序的命中项 {score, platform, tids, topics, text}
    """
    q_tokens, q_weights = rule_query(rule)
    if not q_tokens:
        return []
    hits = []
    for i, toks in enumerate(token_sets):
        s = score_item(q_tokens, q_weights, toks, idf)
        if s >= HIT_MIN:
            hits.append((s, i))
    hits.sort(reverse=True)
    out = []
    for s, i in hits[:TOP_N]:
        it = items[i]
        out.append({
            "score": round(s, 3),
            "platform": sorted(it["platforms"])[0],
            "tids": sorted(it["tids"]),
            "topics": it["topics"],
            "text": it["text"][:160],
        })
    return out


# ==== 证据定级 ====

def grade(hits, rule, img_index, tid_index):
    """定证据等级：**人审锚点定基线，检索只做旁证**（2026-11-01 修订）。

    ★ 为什么这么改（实测）：
      - 只用检索定级时，HIT_MIN=0.15 下命中数从 0–2 跳到 106–201，几乎每条都成了 strong，
        这是"假强共识"，比过严更危险；
      - 只用锚点定级时，检索完全没用上。
      折中：等级由**提炼者声明的 anchors**（手册已做过"多篇一致"归并，可追溯）决定；
      检索只负责一件事——**把孤例升级成弱共识**（≥3 条高分旁证 + 跨平台），
      以及给出"这条规则在语料里还有哪些相关条目"的线索。

    规则（plan.md §三）：
        declared 有效 tid ≥3 → strong；==2 → weak；≤1 → single
        升级：single +（高分旁证 ≥3 且跨平台）→ weak
        封顶：anchors 里存在 hard_gap / md_empty，或规则自述 img_dependent → 最高 weak

    返回：
        dict{level, n_declared, n_corroborated, by_platform, cross_lib,
             year_min, year_max, capped_by_gap, missing_anchors, n_hits, upgraded}
    """
    declared = [str(t) for t in (rule.get("anchors") or [])]
    valid, missing = [], []
    cap = "strong"
    capped_by = []
    if rule.get("img_dependent"):
        cap = "weak"
        capped_by.append("img_dependent")

    for t in declared:
        if t not in tid_index:
            missing.append(t)
            continue
        valid.append(t)
        if (img_index.get(t) or {}).get("evidence_cap") == "weak":
            cap = "weak"
            capped_by.append(t)

    strong_hits = [h for h in hits if h["score"] >= CORROBORATE_MIN]
    n_decl = len(valid)
    level = "strong" if n_decl >= 3 else ("weak" if n_decl == 2 else "single")

    # ★ 修（2026-11-01）：必须尊重提炼者的 evidence_hint 作为**上限**。
    #   实测踩过：`tuoke-023` 提炼者已判定"孤例（同批误召回）"，但它挂着 3 个锚点，
    #   纯按锚点数会算成 strong —— 等于把误召回洗成强共识。提炼者说孤例就按孤例。
    _order = {"single": 0, "weak": 1, "strong": 2}
    hint = rule.get("evidence_hint")
    capped_by_hint = False
    if hint in _order and _order[hint] < _order[level]:
        level = hint
        capped_by_hint = True

    # ---- 只有"孤例"允许被旁证升级，且要求跨平台 ----
    platforms = {(tid_index.get(t) or {}).get("platform", "?") for t in valid}
    for h in strong_hits:
        platforms.add(h["platform"])
    cross_lib = len({p for p in platforms if p and p != "?"}) > 1
    upgraded = False
    if level == "single" and len(strong_hits) >= 3 and cross_lib and hint != "single":
        level = "weak"
        upgraded = True
    if level == "strong" and cap == "weak":
        level = "weak"

    years = [(tid_index.get(t) or {}).get("year") for t in valid]
    years = [y for y in years if y]
    return {
        "level": level,
        "n_declared": n_decl,
        "n_corroborated": len(strong_hits),
        "n_tids": n_decl,                       # 兼容旧字段含义：声明锚点数
        "by_platform": {p: sum(1 for t in valid if (tid_index.get(t) or {}).get("platform") == p)
                        for p in {p for p in platforms if p and p != "?"}},
        "cross_lib": cross_lib,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "capped_by_gap": capped_by,
        "capped_by_hint": capped_by_hint,
        "missing_anchors": missing,
        "n_hits": len(hits),
        "upgraded": upgraded,
    }


# ==== 主流程 ====

def process_draft(path, doc, items, token_sets, idf, img_index, tid_index):
    """处理一份规则草案，返回带证据的规则列表。"""
    rules = doc.get("rules") or []
    print(f"[证据] {path.name}：{len(rules)} 条规则")
    out = []
    single_list = []
    for k, rule in enumerate(rules, start=1):
        hits = retrieve(rule, items, token_sets, idf)
        ev = grade(hits, rule, img_index, tid_index)
        if ev["level"] == "single":
            single_list.append(rule.get("id"))
        merged = dict(rule)
        merged["evidence"] = ev
        merged["top_hits"] = hits[:8]
        out.append(merged)
        print(f"[证据]   {k:>2}/{len(rules)} {rule.get('id','?'):<12} {ev['level']:<6} "
              f"锚点={ev['n_declared']:<3} 旁证={ev['n_corroborated']:<3} "
              f"线索={ev['n_hits']:<4} 跨库={'是' if ev['cross_lib'] else '否'}"
              f"{' ↑旁证升级' if ev['upgraded'] else ''}"
              f"{' 缺口封顶' if ev['capped_by_gap'] else ''}")
    result = {k: v for k, v in doc.items() if k != "rules"}
    result["rules"] = out
    outp = common.OUT_DIR / "drafts" / f"{path.stem.replace('.rules','')}.evidence.json"
    outp.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[证据] → {outp}")
    if single_list:
        print(f"[证据] ⚠ 孤例（≤1 独立来源，只能进暂存区）：{', '.join(single_list)}")
    return result, outp


def write_table(results):
    """生成人读的证据表（每条规则一行）。"""
    lines = ["# 规则证据表（人审锚点定基线 + 检索旁证）", ""]
    for doc in results:
        lines.append(f"## {doc.get('theme','?')}")
        lines.append("")
        lines.append("| id | 等级 | 锚点 | 旁证(≥%.2f) | 线索 | 跨库 | 年份 | 封顶 | 标题 |" % CORROBORATE_MIN)
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in doc["rules"]:
            ev = r["evidence"]
            yrs = f"{ev['year_min']}–{ev['year_max']}" if ev["year_min"] else "—"
            cap = "/".join(str(c) for c in ev["capped_by_gap"]) or "—"
            tag = ev["level"]
            if ev.get("upgraded"):
                tag += " ↑"
            lines.append(
                f"| `{r.get('id','?')}` | {tag} | {ev['n_declared']} | {ev['n_corroborated']} | "
                f"{ev['n_hits']} | {'是' if ev['cross_lib'] else '否'} | {yrs} | {cap} | "
                f"{r.get('title','')[:40]} |")
        bad = [r.get("id") for r in doc["rules"] if r["evidence"]["missing_anchors"]]
        if bad:
            lines += ["", f"⚠ 悬空锚点（declared 但查不到该 tid）：{', '.join(str(b) for b in bad)}"]
        lines.append("")
    p = common.OUT_DIR / "drafts" / "证据表.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[证据] 人读表 → {p}")


def run():
    """主流程：载入语料与草案 → 逐条检索定级 → 落盘。"""
    drafts = load_rules()
    if not drafts:
        print(f"[证据] 没有找到草案（{common.OUT_DIR / 'drafts'}\\{DRAFT_GLOB}），先跑规则提炼")
        return None
    items, token_sets, idf = load_corpus()
    img_index = load_img_index()
    tid_index = common.build_tid_index()
    results = []
    for path, doc in drafts:
        res, _ = process_draft(path, doc, items, token_sets, idf, img_index, tid_index)
        results.append(res)
    write_table(results)

    lv = Counter(r["evidence"]["level"] for d in results for r in d["rules"])
    print(f"\n==== 证据分布 ==== {dict(lv)}")
    return results


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
