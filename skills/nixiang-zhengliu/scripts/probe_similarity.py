"""probe_similarity.py —— 相似度函数选型的对照实验（不是交付物，是调参依据）。

用途：
    merge_pools.py 用「字符三元组 Jaccard」找跨库同簇，实测跨库召回≈0（压缩 1.0×）。
    本脚本在同一批数据上并列比较三种相似度，用人工可判的样例决定该用哪个：

      A. 字符三元组 Jaccard（原方案）
      B. ASCII 技术指纹 Jaccard（标识符 / 报错码 / 命令 / 文件名 / API 名）
      C. 稀有中文二元组 Jaccard（df 在 [2, DF_MAX] 之间的中文 bigram）

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"
    uv run --no-project python scripts\\probe_similarity.py 脱壳加固

关键结论 / 限制：
    - 只看单个主题（默认 脱壳加固），输出的是"候选最高分对"，需要人眼判断是否真的同一条经验。
    - 【未验证】样例够不够代表全库，要等样板主题蒸馏完再回看。
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict

import common
import merge_pools

# ASCII 技术指纹：标识符、报错码、命令、文件/类/方法名、十六进制
_RE_ASCII = re.compile(r"[A-Za-z][A-Za-z0-9_.\-/$#:]{2,}")
_RE_HEX = re.compile(r"0x[0-9a-fA-F]{4,}")
_RE_CJK = re.compile(r"[\u4e00-\u9fff]")
_RE_YEAR = re.compile(r"^(19|20)\d{2}$")

DF_MAX = 400          # 中文 bigram 的 document frequency 上限（超过视为"太普通，无区分度"）


def ascii_tokens(text):
    """抽取 ASCII 技术指纹（小写归一，去纯年份）。"""
    toks = {m.group(0).lower() for m in _RE_ASCII.finditer(text)}
    toks |= {m.group(0).lower() for m in _RE_HEX.finditer(text)}
    return {t for t in toks if not _RE_YEAR.match(t)}


def cjk_bigrams(text):
    """抽取中文二元组（跳过非中文邻接）。"""
    out = set()
    cjk = _RE_CJK.findall(text)
    s = "".join(cjk)
    for i in range(len(s) - 1):
        out.add(s[i:i + 2])
    return out


def jac(a, b):
    """集合 Jaccard。"""
    if not a or not b:
        return 0.0
    i = len(a & b)
    return i / len(a | b) if i else 0.0


def main(theme):
    """在指定主题上并列比较三种相似度，打印高分候选对。"""
    items = merge_pools.load_52pj_items() + merge_pools.load_kanxue_items()
    theme_items = []
    for it in items:
        if theme in it["topics"]:
            theme_items.append(it)
    p52 = [i for i in theme_items if common.P_52PJ in i["platforms"]]
    pkx = [i for i in theme_items if common.P_KX in i["platforms"]]
    print(f"[对照] 主题「{theme}」：52pj {len(p52):,} 条，kanxue {len(pkx):,} 条")

    for it in theme_items:
        it["ascii"] = ascii_tokens(it["text"])
        it["cjk"] = cjk_bigrams(it["text"])

    # 稀有中文 bigram 的 df 过滤
    df = Counter()
    for it in theme_items:
        for g in it["cjk"]:
            df[g] += 1
    for it in theme_items:
        it["cjk_rare"] = {g for g in it["cjk"] if 2 <= df[g] <= DF_MAX}

    # 抽样：取 12 条 kanxue 条目，各自找 52pj 最高分的 1 条
    step = max(1, len(pkx) // 12)
    print(f"\n{'='*100}")
    for probe in pkx[::step][:12]:
        best = {"A": (0, None), "B": (0, None), "C": (0, None)}
        for cand in p52:
            sa = jac(probe["grams"], cand["grams"])
            if sa > best["A"][0]:
                best["A"] = (sa, cand)
            sb = jac(probe["ascii"], cand["ascii"])
            if sb > best["B"][0]:
                best["B"] = (sb, cand)
            sc = jac(probe["cjk_rare"], cand["cjk_rare"])
            if sc > best["C"][0]:
                best["C"] = (sc, cand)
        print(f"\n--- kanxue: {probe['text'][:150]}")
        for k, label in (("A", "字符三元组"), ("B", "ASCII指纹"), ("C", "稀有中文二元组")):
            s, c = best[k]
            if c is None:
                print(f"  [{k}] {label:<14} 无")
                continue
            shared = ""
            if k == "B":
                shared = " 共用指纹=" + ",".join(sorted(probe["ascii"] & c["ascii"])[:6])
            elif k == "C":
                shared = " 共用bigram=" + ",".join(sorted(probe["cjk_rare"] & c["cjk_rare"])[:6])
            print(f"  [{k}] {label:<14} {s:.3f}{shared}")
            print(f"       ↳ {c['text'][:130]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "脱壳加固")
