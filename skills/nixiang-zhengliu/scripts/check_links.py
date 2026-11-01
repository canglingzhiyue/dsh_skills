"""check_links.py —— 树的悬空引用检查（类比 reverse-skill-router 的 scan-capabilities 悬空检查）。

检查四件事：
    1. **内部链接**：`[文字](references/xxx.md)` / `[文字](references/xxx.md#tuoke-001)`
       —— 目标文件必须存在；带锚点的，锚点必须在目标文件里真的存在（`#### tuoke-001` 或 `id="..."`）。
    2. **孤儿文件**：`references\\` 下每个主题文件都必须能从句根 SKILL.md 链到；
       链不到 = 孤儿，路由不进去就等于白写（WARN 级别，不算 FAIL）。
    3. **锚点表 tid 有效性**：锚点 TSV 每行的 tid 必须能在 tid 索引里查到（死链 = FAIL）。
    4. **症状索引目标有效性**：每行必须指向真实存在的 `文件#锚点`（FAIL）。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\check_links.py [树目录]

    退出码：0 = 无 FAIL；1 = 有 FAIL。

关键结论 / 限制：
    - 锚点约定：规则节点渲染成 `#### <rule-id> <标题>`，链接写 `#<rule-id>`；也认 `id="..."`。
    - 锚点表/症状索引的文件名靠关键词识别（含「锚点」「症状」），改名要同步 INDEX_KEYWORDS。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import common

DEFAULT_TREE = common.OUT_DIR / "nixiang-shu"
INDEX_KEYWORDS = ("症状", "锚点")

_RE_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_RE_RULE_ID = re.compile(r"^#{2,5}\s+([a-z]+-\d{3})\b", re.M)
_RE_ID_ATTR = re.compile(r'id="([^"]+)"')


def file_anchors(path: Path):
    """抽一个 md 文件里**真实可跳转**的锚点集合。

    ★ 2026-11-01 评审修复：原来把"标题以 id 开头"（`#### tuoke-001 标题`）也算作锚点，
      但 Markdown 自动锚点其实长成 `#tuoke-001-标题`，链接写 `#tuoke-001` 在真实渲染里
      **跳不过去**；而闸门因为自己的宽松语义永远 PASS。现在**只认显式 `<a id="...">`**，
      渲染侧已在每条规则前插入该标签（render_tree._rule_lines）。
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    return set(_RE_ID_ATTR.findall(text))


def check_internal_links(tree: Path):
    """检查所有 md 的内部相对链接与锚点。返回 [(level, msg)]。"""
    out = []
    md_files = sorted(tree.rglob("*.md"))
    bad_file = 0
    bad_anchor = 0
    checked = 0
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in _RE_LINK.findall(text):
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            checked += 1
            target, _, anchor = raw.partition("#")
            tpath = (md.parent / target).resolve() if target else md
            if not tpath.exists():
                bad_file += 1
                out.append(("FAIL", f"{md.relative_to(tree)} → 目标不存在：{raw}"))
                continue
            if anchor and tpath.suffix == ".md":
                if anchor not in file_anchors(tpath):
                    bad_anchor += 1
                    out.append(("FAIL", f"{md.relative_to(tree)} → 锚点不存在：{raw}"))
    out.insert(0, ("OK" if not (bad_file or bad_anchor) else "FAIL",
                   f"内部链接 {checked} 条：目标缺失 {bad_file}、锚点缺失 {bad_anchor}"))
    return out


def check_orphans(tree: Path):
    """references 下的文件是否**从根可达**（沿 md 链接做传递闭包）。

    ★ 修（2026-11-01）：原来只比对"文件名是否出现在根 SKILL.md 里"，
    主题按阶段拆分后，阶段文件是经 `references/<主题>.md` 索引页转链的，
    根里当然不出现它们的名字 —— 那是正常结构，不该报孤儿。
    改为：从 SKILL.md 出发 BFS 沿链接遍历，走不到的才算真孤儿。
    """
    root = tree / "SKILL.md"
    if not root.exists():
        return [("FAIL", "缺根 SKILL.md，无法做孤儿检查")]

    reachable = set()
    queue = [root.resolve()]
    seen = set()
    while queue:
        cur = queue.pop()
        if cur in seen or not cur.exists() or cur.suffix != ".md":
            continue
        seen.add(cur)
        reachable.add(cur)
        try:
            text = cur.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in _RE_LINK.findall(text):
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            target = raw.partition("#")[0]
            if not target:
                continue
            tpath = (cur.parent / target).resolve()
            if tpath not in seen:
                queue.append(tpath)

    refs = sorted(p for p in (tree / "references").rglob("*.md")) if (tree / "references").exists() else []
    orphans = [p for p in refs if p.resolve() not in reachable]
    out = [("OK" if not orphans else "WARN",
            f"references 文件 {len(refs)} 个，从根不可达 {len(orphans)} 个")]
    for p in orphans:
        out.append(("WARN", f"  ↳ {p.relative_to(tree)}"))
    return out


def check_anchor_tids(tree: Path, tid_index):
    """锚点表每行的 tid 必须存在。"""
    out = []
    # ★ 修（2026-11-01）：锚点表是 `锚点/<主题>.tsv`，文件名本身不含「锚点」，
    #   原来只匹配 p.name 会漏检整套锚点表。这里连父目录名一起匹配。
    files = [p for p in tree.rglob("*")
             if p.is_file() and ("锚点" in p.name or "锚点" in p.parent.name)]
    if not files:
        return [("SKIP", "没有锚点表文件，跳过")]
    total = 0
    dead = 0
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            if not ln.strip() or ln.startswith("#"):
                continue
            # 锚点表是 TSV（制表符），早期草案也可能写成竖线分隔——两种都认
            cells = [c.strip() for c in re.split(r"\t|\||｜", ln)]
            tid = next((c for c in cells if c.isdigit() and len(c) >= 5), "")
            if not tid:
                continue
            total += 1
            if tid not in tid_index:
                dead += 1
                if dead <= 10:
                    out.append(("FAIL", f"{p.name} → 死锚点 tid={tid}"))
    out.insert(0, ("OK" if dead == 0 else "FAIL", f"锚点表 {len(files)} 个：tid {total} 行，死链 {dead}"))
    return out


def check_symptom_targets(tree: Path):
    """症状索引每行必须指向真实存在的 文件#锚点。"""
    out = []
    # 症状索引按主题拆分后放在 `症状索引/<主题>.md`，文件名里不含"症状" → 连父目录名一起匹配
    files = [p for p in tree.rglob("*")
             if p.is_file() and ("症状" in p.name or "症状" in p.parent.name)]
    if not files:
        return [("SKIP", "没有症状索引文件，跳过")]
    total = 0
    bad = 0
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            for raw in _RE_LINK.findall(ln):
                if raw.startswith(("http://", "https://")):
                    continue
                total += 1
                target, _, anchor = raw.partition("#")
                tpath = (p.parent / target).resolve()
                if not tpath.exists():
                    bad += 1
                    out.append(("FAIL", f"{p.name} → 目标不存在：{raw}"))
                elif anchor and anchor not in file_anchors(tpath):
                    bad += 1
                    out.append(("FAIL", f"{p.name} → 锚点不存在：{raw}"))
    out.insert(0, ("OK" if bad == 0 else "FAIL", f"症状索引 {len(files)} 个：链接 {total} 条，坏链 {bad}"))
    return out


def run(tree: Path):
    """执行全部检查。"""
    if not tree.exists():
        print(f"[链接] SKIP 树目录不存在：{tree}")
        return True
    tid_index = common.build_tid_index()
    results = []
    results += check_internal_links(tree)
    results += check_orphans(tree)
    results += check_anchor_tids(tree, tid_index)
    results += check_symptom_targets(tree)
    print(f"[链接] 检查目标：{tree}")
    for level, msg in results:
        print(f"[链接] {level:<4} {msg}")
    ok = all(level != "FAIL" for level, _ in results)
    print(f"[链接] 结论：{'OK 无悬空引用' if ok else 'FAIL 有悬空引用'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TREE) else 1)
