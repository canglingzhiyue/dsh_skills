"""build_img_index.py —— 量化「图片未采集」的缺口，并给出可回补清单。

背景（实测 2026-11-01）：
    笔记正文里几乎**没有**图片 URL —— 52pojie 4999 篇里只有 18 篇含图床 URL、4 篇含 markdown 图链；
    kanxue 1754 篇里 0 篇。但两库 `raw/threads/<tid>.json` 的 `images` 字段里**完整保留了图片地址**：
      · 52pojie：`images` = 绝对 URL 列表（https://attach.52pojie.cn/forum/...），另有 `attachments`（相对链接）
      · kanxue ：`images` = [{src: "upload/attach/202310/xxx.webp", alt, from}]，相对路径
    所以「图丢了」的准确说法是 **URL 没进笔记，原始存档还在** → 可按需回补，不必重爬。

本脚本做什么：
    1. 扫两库 raw/threads，产出 tid → 图片清单（张数 + URL + 附件数）；
    2. 扫两库笔记正文，数「见原帖图 / 如下图 / 图中」这类指向图片的字样，得到**图文依赖度**；
    3. 交叉出三类笔记并落盘：
       · 有图引用 + raw 里有 URL  → **可回补**（按需下载）
       · 有图引用 + raw 里无 URL  → **真缺口**（外链图/图床失效，无法回补，必须降证据等级）
       · 无图引用                → 不受影响
    4. 打印统计，供决定"补多少张、补哪些"。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"; $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\build_img_index.py

关键结论 / 限制：
    - 纯本地，不联网、不下载。要不要真去抓图是另一个决策（涉及重新访问目标站与风控）。
    - 图文依赖度用正则命中计数，是**下限估计**：作者可能只写"如图所示"而不含上述字样。
    - 【未验证】"关键信息在图里"的判定无法自动完成，需人工/看图确认；本脚本只给候选清单。
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter

import common

RAW_52PJ = common.LIB_52PJ / "raw" / "threads"
RAW_KX = common.LIB_KX / "raw" / "threads"
KX_IMG_PREFIX = "https://bbs.kanxue.com/"

# 指向图片的字样（下限估计，见文件头「限制」）
_RE_IMG_REF = re.compile(r"见原帖图|如下图|如图所示|上图|下图|图中|截图|贴图|看图")
_RE_IMG_REF_N = re.compile(r"见原帖图\s*(\d+)")

# 关键章节：这些节里出现图片引用，才真正影响蒸馏可信度
KEY_SECTIONS = ("## 3.", "## 5.", "## 6.")


_RE_MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
_RE_HTML_IMG = re.compile(r"<img[^>]+src=[\"']([^\"']+)")


def _abs_url(src, platform):
    """把图片地址补成绝对 URL（kanxue 存的是相对路径）。"""
    src = (src or "").strip()
    if not src:
        return ""
    if src.startswith("http"):
        return src
    src = src.lstrip("./").lstrip("/")
    base = KX_IMG_PREFIX if platform == common.P_KX else "https://www.52pojie.cn/"
    return base + src


def load_raw_images(path, platform):
    """读一条 raw/threads JSON，返回图片清单。

    ★ 关键坑（实测 2026-11-01）：kanxue 的 `images` 字段**大量为空**（抽样 5 篇 hard_gap 全是 0），
    但 raw 的 `markdown` 正文里图链是完整的（`![](upload/attach/...)`）。
    这是采集端的抽取缺陷，不是数据丢失 —— 所以字段为空时必须回落到 markdown 正则。

    参数：
        path     —— raw JSON 路径
        platform —— common.P_52PJ / common.P_KX
    返回：
        dict{tid, n_images, urls, n_att, ok, from_md} 或 None（解析失败/非正文）
    """
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(obj, dict):
        return None
    tid = str(obj.get("tid") or path.stem).strip()
    ok = bool(obj.get("ok", True)) and not obj.get("blocked") and not obj.get("riskBlocked")

    urls = []
    for it in obj.get("images") or []:
        if isinstance(it, str):
            urls.append(_abs_url(it, platform))
        elif isinstance(it, dict):
            urls.append(_abs_url(it.get("src"), platform))

    # ---- 回落：从 markdown 正文里再抽一遍 ----
    from_md = False
    md = obj.get("markdown") or ""
    md_urls = [_abs_url(m.group(1), platform) for m in _RE_MD_IMG.finditer(md)]
    md_urls += [_abs_url(m.group(1), platform) for m in _RE_HTML_IMG.finditer(md)]
    if md_urls:
        before = len({u for u in urls if u})
        urls += md_urls
        if len({u for u in urls if u}) > before:
            from_md = True

    uniq = list(dict.fromkeys(u for u in urls if u))
    n_att = len(obj.get("attachments") or []) if platform == common.P_52PJ else len(obj.get("codes") or [])
    return {"tid": tid, "n_images": len(uniq), "urls": uniq, "n_att": n_att,
            "ok": ok, "from_md": from_md, "md_len": len(md)}


def scan_raw(root, platform):
    """扫一个 raw/threads 目录，返回 tid → 图片清单。"""
    out = {}
    n = 0
    n_from_md = 0
    n_empty_md = 0
    for p in sorted(root.glob("*.json")):
        rec = load_raw_images(p, platform)
        if rec:
            out[rec["tid"]] = rec
            n += 1
            if rec["from_md"]:
                n_from_md += 1
            if rec["md_len"] == 0:
                n_empty_md += 1
    print(f"[图片] {platform} raw 正文 {n:,} 篇｜靠 markdown 回落补出图链 {n_from_md:,} 篇｜"
          f"正文为空 {n_empty_md:,} 篇")
    return out


def section_img_refs(note_text):
    """数笔记里指向图片的字样，并单独统计关键章节内的命中。

    返回：
        dict{refs: 总命中, refs_key: 关键章节命中, max_n: 「见原帖图 N」的最大 N}
    """
    refs = _RE_IMG_REF.findall(note_text)
    refs_key = 0
    idx = [note_text.find(s) for s in KEY_SECTIONS if note_text.find(s) >= 0]
    if idx:
        lo, hi = min(idx), len(note_text)
        seg = note_text[lo:hi]
        refs_key = len(_RE_IMG_REF.findall(seg))
    ns = [int(x) for x in _RE_IMG_REF_N.findall(note_text)]
    return {"refs": len(refs), "refs_key": refs_key, "max_n": max(ns) if ns else 0}


def main():
    """主流程：raw 图片清单 + 笔记图文依赖度 → 交叉分类 → 落盘统计。"""
    raw = {}
    raw.update(scan_raw(RAW_52PJ, common.P_52PJ))
    raw.update(scan_raw(RAW_KX, common.P_KX))

    notes = {}
    for notes_dir, platform in ((common.NOTES_52PJ, common.P_52PJ), (common.NOTES_KX, common.P_KX)):
        for p in sorted(notes_dir.glob("*.md")):
            if p.name == "INDEX.md":
                continue
            tid = p.stem.split("-")[0]
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            notes[tid] = {"platform": platform, **section_img_refs(text)}

    index = {}
    buckets = Counter()
    per_platform = Counter()
    caps = Counter()
    md_empty = 0
    for tid, meta in notes.items():
        rec = raw.get(tid) or {}
        n_images = rec.get("n_images", 0)
        has_raw = tid in raw
        md_empty_flag = has_raw and rec.get("md_len", 0) == 0
        ent = {
            "platform": meta["platform"],
            "img_refs": meta["refs"],
            "img_refs_key": meta["refs_key"],
            "max_img_n": meta["max_n"],
            "n_images": n_images,
            "n_att": rec.get("n_att", 0),
            "urls": rec.get("urls", []),
            "has_raw": has_raw,
            "md_empty": md_empty_flag,
        }
        if meta["refs"] == 0:
            status = "no_ref"                       # 不依赖图
        elif n_images > 0:
            status = "refillable"                   # 依赖图，且 raw 里有 URL → 可回补
        else:
            status = "hard_gap"                     # 依赖图，但没拿到任何图 → 真缺口
        ent["status"] = status

        # ---- 证据上限（口径见 plan.md §三，2026-11-01 修订）----
        # ★ 修订理由：原口径把 refillable 也压成 weak，导致 72% 的锚点全部降级、
        #   35/37 条规则一律 weak，strong 永远不可能出现——闸门变成了噪声。
        #   正确做法：笔记层只对**数据真缺**的压等级（hard_gap / md_empty）；
        #   "判据是否在截图里"由规则字段 img_dependent 决定，不由笔记层一刀切。
        if status == "hard_gap" or md_empty_flag:
            ent["evidence_cap"] = "weak"
        else:
            ent["evidence_cap"] = "strong"
        caps[ent["evidence_cap"]] += 1
        if md_empty_flag:
            md_empty += 1

        index[tid] = ent
        buckets[status] += 1
        per_platform[(meta["platform"], status)] += 1

    out = common.DATA_DIR / "img_index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    tot_imgs = sum(v.get("n_images", 0) for v in raw.values())
    print("\n==== 图片缺口量化 ====")
    print(f"有笔记的 tid          {len(notes):,}")
    print(f"raw 里有正文的 tid    {len(raw):,}")
    print(f"两库图片总数          {tot_imgs:,}")
    print(f"不依赖图              {buckets['no_ref']:,}")
    print(f"依赖图 + 可回补       {buckets['refillable']:,}")
    print(f"依赖图 + 真缺口       {buckets['hard_gap']:,}")
    print(f"正文 markdown 为空    {md_empty:,}  ← 这批笔记是从 bodyText 产的，无代码块/无图")
    print(f"证据上限 strong/weak  {caps['strong']:,} / {caps['weak']:,}")
    print(f"索引 → {out}")
    for (plat, st), c in sorted(per_platform.items()):
        print(f"  {plat:<7} {st:<11} {c:,}")

    # 回补成本估计：只补"关键章节提到图"的，且每篇只补前 N 张
    key_ref = [t for t, v in index.items() if v["img_refs_key"] > 0 and v["n_images"] > 0]
    print(f"\n关键章节提到图且可回补 {len(key_ref):,} 篇｜若每篇补 8 张 ≈ {len(key_ref)*8:,} 张")
    return index


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
