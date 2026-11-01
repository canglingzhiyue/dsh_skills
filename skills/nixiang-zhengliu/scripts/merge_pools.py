"""merge_pools.py —— 两库经验池统一口径：IDF 加权去重 + 建检索索引 + 证据统计。

用途：
    (1) 把两库经验池拉到同一层，做**去重**（kanxue 已内部去重；52pojie 的 29999 条是平铺的，
        存在同一作者系列贴反复表述同一条经验的情况）；
    (2) 给每条经验算好 token 集与 IDF 表，供后续「规则级证据计数」直接复用。

为什么不用字符 n-gram 直接聚簇（实测，2026-11-01）：
    probe_similarity.py 在「脱壳加固」主题上并列比较三种相似度：
      · 字符三元组 Jaccard：跨库最高分只有 0.02–0.12，**跨库召回为零**；
      · ASCII 指纹 Jaccard：单个通用词（root / dex / dump）就能给到 1.000，**假阳性严重**；
      · 稀有中文二元组：0.07–0.13，共用的是「必须/否则/避免」这类虚词。
    结论：**跨平台逐句"同簇"在句级不存在**——两库的人不会用同一句话讲同一件事。
    因此「跨库同簇 = 强共识」的正确实现是**规则级证据计数**（见 build_evidence_index 的规划），
    本脚本只承担"同平台近似去重 + 备好 IDF 与 token 集"。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"; $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\merge_pools.py

关键结论 / 限制：
    - IDF 加权 Jaccard 是去重手段，不是语义判定；阈值 WJ_MIN 偏松会把"同主题不同建议"合掉。
    - 【未验证】WJ_MIN=0.55 需在样板主题（脱壳加固）上人工抽查 30 簇校准后回调。
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict

import common

# ==== 调参旋钮 ====
DF_MIN = 2                   # 出现 1 次的 token 无区分度，靠它找不到任何邻居
DF_MAX_ASCII = 2000          # ASCII token 的 df 上限（超过即视为通用词，如 root / dex / adb）
DF_MAX_CJK = 600             # 中文 3-gram 的 df 上限（超过即视为套话，如「必须注意」「这种情况」）
BUCKET_CAP = 300             # 单个倒排桶上限，超过直接弃（防爆炸）
CANDIDATE_CAP = 6_000_000    # 候选对硬上限
RARE_ANCHOR = 6              # 每条只拿 IDF 最高的 N 个 token 做前缀锚（经典 prefix filtering）
WJ_MIN = 0.55                # IDF 加权 Jaccard 阈值
CJK_N = 3                    # 中文 token 长度：3 比 2 更具体，实测 2 命中虚词

_RE_ASCII = re.compile(r"[A-Za-z][A-Za-z0-9_.\-/$#:]{2,}")
_RE_HEX = re.compile(r"0x[0-9a-fA-F]{4,}")
_RE_CJK = re.compile(r"[\u4e00-\u9fff]+")
_RE_YEAR = re.compile(r"^(19|20)\d{2}$")


# ==== 载入 ====

def load_52pj_items():
    """载入 52pojie 经验池，产出 item 列表（按 (tid, 归一文本) 去重）。

    返回：
        list[dict]：text / norm / platforms / tids / topics
    """
    pool = json.loads(common.POOL_52PJ.read_text(encoding="utf-8"))
    seen = set()
    items = []
    for _topic_key, records in (pool.get("by_topic") or {}).items():
        for rec in records or []:
            tid = str(rec.get("tid", "")).strip()
            points = rec.get("points") or []
            if isinstance(points, str):
                points = [points]
            topics = common.map_topics(rec.get("topics") or [])
            for pt in points:
                if not isinstance(pt, str) or len(pt.strip()) < 12:
                    continue
                text = pt.strip()
                norm = common.normalize(text)
                if not norm:
                    continue
                if (tid, norm) in seen:      # 同篇笔记在多个主题键下重复出现
                    continue
                seen.add((tid, norm))
                items.append({
                    "text": text, "norm": norm,
                    "platforms": {common.P_52PJ},
                    "tids": {tid} if tid else set(),
                    "topics": topics,
                })
    print(f"[蒸馏] 52pojie 条目 {len(items):,}")
    return items


def load_kanxue_items():
    """载入 kanxue 经验池（已是簇），展开成 item 列表。

    返回：
        list[dict]，tids 取该簇的 sources 全量
    """
    pool = json.loads(common.POOL_KX.read_text(encoding="utf-8"))
    seen = set()
    items = []
    for topic_key, clusters in pool.items():
        if not isinstance(clusters, list):
            continue
        for cl in clusters:
            if not isinstance(cl, dict):
                continue
            text = (cl.get("text") or "").strip()
            if len(text) < 12:
                continue
            norm = common.normalize(text)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            tids = {str(t).strip() for t in (cl.get("sources") or []) if str(t).strip()}
            items.append({
                "text": text, "norm": norm,
                "platforms": {common.P_KX},
                "tids": tids,
                "topics": common.map_topics([topic_key]),
            })
    print(f"[蒸馏] kanxue 条目 {len(items):,}（其经验池本身已是簇）")
    return items


# ==== token 与 IDF ====

def tokenize(text):
    """抽 token：ASCII 技术指纹（小写）+ 十六进制 + 中文 N-gram。

    参数：
        text —— 原始文本
    返回：
        dict{'ascii': set[str], 'cjk': set[str]}
    """
    ascii_toks = {m.group(0).lower() for m in _RE_ASCII.finditer(text)}
    ascii_toks |= {m.group(0).lower() for m in _RE_HEX.finditer(text)}
    ascii_toks = {t for t in ascii_toks if not _RE_YEAR.match(t) and len(t) >= 3}
    cjk_toks = set()
    for run in _RE_CJK.findall(text):
        for i in range(len(run) - CJK_N + 1):
            cjk_toks.add(run[i:i + CJK_N])
    return {"ascii": ascii_toks, "cjk": cjk_toks}


def build_idf(items):
    """统计 df 并算 IDF，同时按 df 上下限筛出可用的"信息型 token"。

    返回：
        (token_sets, idf) —— token_sets[i] = set[str]（已过滤），idf[token] = float
    """
    df = Counter()
    raw = []
    for it in items:
        toks = tokenize(it["text"])
        raw.append(toks)
        for t in toks["ascii"]:
            df[("a", t)] += 1
        for t in toks["cjk"]:
            df[("c", t)] += 1

    n = len(items)
    idf = {}
    token_sets = []
    for toks in raw:
        keep = set()
        for kind, df_max in (("a", DF_MAX_ASCII), ("c", DF_MAX_CJK)):
            for t in toks["ascii"] if kind == "a" else toks["cjk"]:
                d = df[(kind, t)]
                if DF_MIN <= d <= df_max:
                    keep.add(t)
                    idf[t] = math.log((n + 1) / (d + 1)) + 1.0
        token_sets.append(keep)
    print(f"[蒸馏] token 词表 {len(idf):,}（已按 df∈[{DF_MIN},{DF_MAX_ASCII}/{DF_MAX_CJK}] 过滤）")
    return token_sets, idf


# ==== 去重聚类 ====

def candidate_pairs(token_sets, idf):
    """前缀锚定生成候选对：每条只把 IDF 最高的 RARE_ANCHOR 个 token 放进桶。

    为什么这么做（实测 2026-11-01）：全 token 倒排会撞出 600 万+ 候选对并触顶，
    结果不可信。前缀过滤是集合相似连接的标准做法——若两条相似度够高，它们的
    稀有 token 必然有交集，所以只需在稀有 token 上建桶。

    返回：
        (pairs, stats)
    """
    buckets = defaultdict(list)
    for idx, toks in enumerate(token_sets):
        if not toks:
            continue
        anchors = sorted(toks, key=lambda t: -idf.get(t, 1.0))[:RARE_ANCHOR]
        for t in anchors:
            buckets[t].append(idx)
    pairs = set()
    dropped = 0
    for ids in buckets.values():
        if len(ids) < 2:
            continue
        if len(ids) > BUCKET_CAP:
            dropped += 1
            continue
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                pairs.add((ids[x], ids[y]))
                if len(pairs) > CANDIDATE_CAP:
                    return pairs, {"dropped_buckets": dropped, "capped": True}
    return pairs, {"dropped_buckets": dropped, "capped": False}


def weighted_jaccard(a, b, idf):
    """IDF 加权 Jaccard：通用词权重低，特征词权重高。"""
    if not a or not b:
        return 0.0
    inter = a & b
    if not inter:
        return 0.0
    inter_w = sum(idf.get(t, 1.0) for t in inter)
    union_w = sum(idf.get(t, 1.0) for t in (a | b))
    return inter_w / union_w if union_w else 0.0


def union_find(n, pairs):
    """并查集合并，返回 parent 数组。"""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    return parent


def cluster_items(items, token_sets, idf):
    """完全同文先合并，再按加权 Jaccard 阈值合并近似条目。

    返回：
        (groups, stats)
    """
    pairs = []
    by_norm = defaultdict(list)
    for i, it in enumerate(items):
        by_norm[it["norm"]].append(i)
    for ids in by_norm.values():
        for k in range(1, len(ids)):
            pairs.append((ids[0], ids[k]))
    exact_merged = len(pairs)

    cand, cstats = candidate_pairs(token_sets, idf)
    print(f"[蒸馏] 候选对 {len(cand):,}｜超桶丢弃 {cstats['dropped_buckets']:,} 个｜触顶={cstats['capped']}")
    band = Counter()
    kept = 0
    for i, j in cand:
        sim = weighted_jaccard(token_sets[i], token_sets[j], idf)
        if sim >= 0.40:
            band[round(sim, 1)] += 1
        if sim >= WJ_MIN:
            pairs.append((i, j))
            kept += 1
    if band:
        print("[蒸馏] 分数分布(≥0.40)：" + " ".join(f"{k:.1f}:{v:,}" for k, v in sorted(band.items())))
    print(f"[蒸馏] 精确同文合并 {exact_merged:,} 对｜加权≥{WJ_MIN} 合并 {kept:,} 对")

    parent = union_find(len(items), pairs)
    groups = defaultdict(list)
    for i in range(len(items)):
        groups[parent[i]].append(i)
    return list(groups.values()), {"candidate_pairs": len(cand), "kept_pairs": kept,
                                   "exact_merged": exact_merged}


# ==== 簇记录与统计 ====

def build_clusters(groups, items, tid_index):
    """把分组转成带统计字段的簇记录（字段口径见 plan.md §三）。"""
    clusters = []
    for gi, ids in enumerate(sorted(groups, key=len, reverse=True), start=1):
        members = [items[i] for i in ids]
        rep = max(members, key=lambda m: len(m["text"]))
        tids = {common.P_52PJ: set(), common.P_KX: set()}
        votes = Counter()
        for m in members:
            for p in m["platforms"]:
                tids[p] |= m["tids"]
            for t in m["topics"]:
                votes[t] += 1
        years = [y for p, ts in tids.items() for t in ts
                 if (y := (tid_index.get(t) or {}).get("year"))]
        n_sources = len(tids[common.P_52PJ]) + len(tids[common.P_KX])
        platforms = sorted(p for p, ts in tids.items() if ts)
        topics = [t for t, c in votes.most_common() if c >= max(1, len(members) // 3)][:3] or ["综合实战"]
        clusters.append({
            "cid": f"C{gi:05d}",
            "text": rep["text"],
            "topics": topics,
            "platforms": platforms,
            "cross_lib": len(platforms) > 1,
            "tids": {p: sorted(ts) for p, ts in tids.items()},
            "n_sources": n_sources,
            "members": len(members),
            "consensus": "strong" if n_sources >= 3 else ("weak" if n_sources == 2 else "single"),
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
        })
    return clusters


def summarize(clusters, items, cstats):
    """汇总统计并写盘（clusters.json + cluster_stats.json）。"""
    by_platform = Counter()
    by_consensus = Counter()
    by_topic = defaultdict(Counter)
    for c in clusters:
        by_platform["+".join(c["platforms"]) or "unknown"] += 1
        by_consensus[c["consensus"]] += 1
        for t in c["topics"]:
            by_topic[t][c["consensus"]] += 1
    stats = {
        "input_items": len(items),
        "clusters": len(clusters),
        "compression": round(len(items) / max(1, len(clusters)), 3),
        "dedup_merged": cstats,
        "by_platform": dict(by_platform),
        "by_consensus": dict(by_consensus),
        "cross_lib_clusters": sum(1 for c in clusters if c["cross_lib"]),
        "by_topic": {t: dict(v) for t, v in
                     sorted(by_topic.items(), key=lambda kv: -sum(kv[1].values()))},
        "wj_min": WJ_MIN,
    }
    (common.CLUSTER_DIR / "clusters.json").write_text(
        json.dumps(clusters, ensure_ascii=False, indent=1), encoding="utf-8")
    (common.CLUSTER_DIR / "cluster_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    return stats


def write_report(stats, clusters):
    """写人读的 Markdown 统计报告。"""
    lines = [
        "# 两库经验池统一口径（去重 + 索引）",
        "",
        f"> merge_pools.py ｜ IDF 加权 Jaccard ≥ {stats['wj_min']} ｜ 输入 {stats['input_items']:,} 条 → {stats['clusters']:,} 簇"
        f"（压缩 {stats['compression']}×）",
        "",
        "## 实测结论（2026-11-01）：跨平台逐句同簇不可行",
        "",
        "probe_similarity.py 在「脱壳加固」上并列比较三种相似度，跨库最高分只有 0.02–0.12；",
        "ASCII 指纹用单个通用词就能给出 1.000（假阳性）。**两库不会用同一句话讲同一条经验。**",
        "因此「跨库同簇 = 强共识」改为**规则级证据计数**：先把规则提出来，再用规则的关键词签名",
        "回检索 35k 条原文，数独立来源与平台数（证据索引已落在 `data/clusters/evidence_index.json`）。",
        "",
        "## 一、平台组成",
        "",
        "| 组成 | 簇数 |",
        "|---|---|",
    ]
    for k, v in sorted(stats["by_platform"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v:,} |")
    lines += ["", "## 二、证据分级（按独立来源 tid 数）", "", "| 分级 | 簇数 |", "|---|---|"]
    for k in ("strong", "weak", "single"):
        lines.append(f"| {k} | {stats['by_consensus'].get(k, 0):,} |")
    lines += ["", "## 三、按主题（strong/weak/single）", "",
              "| 主题 | strong | weak | single | 合计 |", "|---|---|---|---|---|"]
    for t, v in stats["by_topic"].items():
        lines.append(f"| {t} | {v.get('strong',0):,} | {v.get('weak',0):,} | {v.get('single',0):,} | {sum(v.values()):,} |")
    path = common.OUT_DIR / "drafts" / "簇统计.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[蒸馏] 报告 → {path}")


def run():
    """主流程：载入 → token/IDF → 去重聚类 → 统计。

    说明：检索索引**不落盘**。35k 条重新 tokenize 只要几秒，落一份 postings 反而会
    产出几十 MB 的中间件（实测估算 50 MB 量级），违背「过程产物可重跑、不留垃圾」的原则。
    """
    items = load_52pj_items() + load_kanxue_items()
    print(f"[蒸馏] 合计条目 {len(items):,}")
    token_sets, idf = build_idf(items)
    groups, cstats = cluster_items(items, token_sets, idf)
    tid_index = common.build_tid_index()
    clusters = build_clusters(groups, items, tid_index)
    stats = summarize(clusters, items, cstats)
    write_report(stats, clusters)

    print("\n==== 指标 ====")
    print(f"输入条目   {stats['input_items']:,}")
    print(f"去重后簇   {stats['clusters']:,}（压缩 {stats['compression']}×）")
    print(f"跨库簇     {stats['cross_lib_clusters']:,}（句级，参考意义有限）")
    print(f"分级       {stats['by_consensus']}")
    return stats


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
