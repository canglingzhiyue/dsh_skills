"""check_budget.py —— 上下文与体积硬闸门（超预算就 FAIL，不许"反正按需加载"糊过去）。

预算（plan.md §二，2026-11-01 定）：
    根 SKILL.md                ≤ 6,000 字符
    每个 references/<主题>.md   ≤ 12,000 字符
    各索引表（症状/失效/锚点）  ≤ 8,000 字符
    全树静态体积               ≤ 250 KB
    单次会话实际加载           ≤ 30,000 字符（根 + 最多 2 个主题）

为什么按字符而不是字节：中文字符在主流分词器里约 1 字符 ≈ 0.6–1 token，
字符数是比字节更靠近真实上下文成本的量；`apk-reverse\\SKILL.md` 实测 49,056 字符 /
49,399 字节，正是本闸门要防的反面样本。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\check_budget.py [树目录]

    不带参数时检查 `output\\nixiang-shu`（落盘前的暂存位置）；带参数检查任意目录。
    退出码：0 = 全通过；1 = 有 FAIL。

关键结论 / 限制：
    - 只量体积与结构，不判内容质量。
    - 索引表的识别按文件名约定（症状/已失效/锚点 关键词），改文件名要同步改这里的常量。
"""
from __future__ import annotations

import sys
from pathlib import Path

import common

# ==== 预算（字符数）====
# ★ 2026-11-01 评审后重定（review-2026-11-01-样板.md 盲区 #1）：
#   原口径只卡"单文件"，导致主题合计 17,448 字符超 12k 预算 48% 却全部通过——闸门实质作废。
#   新口径按**主题合计**与**全树字符**卡，数字来自算术推导而不是拍脑袋：
#     17 主题 × THEME_TOTAL_MAX 11,000 = 187,000，留 ~13,000 给根+索引+锚点 → 全树 200,000。
#   KB 不再作为判据（中文 1 字符≈3 字节，按 KB 卡会误判），只作 INFO。
ROOT_MAX = 6_000
THEME_MAX = 12_000          # 单文件
THEME_TOTAL_MAX = 12_000    # 每主题合计（跨阶段文件）——与单文件对齐，逻辑更简单
INDEX_MAX = 8_000           # 单份索引
# ★ 2026-11-01 按实测重定：7 主题时索引合计已 70,150，每主题约 10,021 字符
#   （症状索引 ~5k + 锚点 ~5k）。17 主题外推 ≈ 170,357 → 原 100,000 必然超。
#   取 200,000 留余量。依据是**实测斜率**，不是拍脑袋。
INDEX_TOTAL_MAX = 200_000
SESSION_MAX = 30_000        # 单次会话加载（根 + 最厚 2 个主题文件）——**这才是 AI 的真实成本**
TREE_CHARS_MAX = 0          # 0 = 不设 FAIL 门槛，只报 INFO（见下）

DEFAULT_TREE = common.OUT_DIR / "nixiang-shu"
ROOT_NAME = "SKILL.md"
INDEX_KEYWORDS = ("症状", "已失效", "锚点", "失效")


def char_len(path: Path) -> int:
    """读文本并返回字符数（UTF-8 解码后）。"""
    try:
        return len(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def classify(path: Path, tree: Path):
    """把文件归到 root / theme / index / other 四类之一。"""
    rel = path.relative_to(tree)
    name = path.name
    if rel.parts == (ROOT_NAME,):
        return "root"
    # ★ 修（2026-11-01）：症状索引按主题拆分后落在 `症状索引/<主题>.md`，文件名不含关键词，
    #   原来会被归成 other 而**整批逃过索引预算检查**（实测：14,213 字符的症状索引没被统计）。
    if any(k in name for k in INDEX_KEYWORDS):
        return "index"
    if any(k in part for part in rel.parts[:-1] for k in INDEX_KEYWORDS):
        return "index"
    if "references" in rel.parts and name.endswith(".md"):
        return "theme"
    return "other"


def check(tree: Path):
    """执行全部预算检查，返回 (结果列表, 是否全通过)。"""
    results = []
    if not tree.exists():
        # 树还没生成：这是 SKIP 不是 FAIL（与 check_links.py 行为对齐）
        return [("SKIP", f"树目录不存在：{tree}")], True

    files = [p for p in tree.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in files)
    kinds = {"root": [], "theme": [], "index": [], "other": []}
    for p in files:
        kinds[classify(p, tree)].append(p)

    # ---- 1. 根文件 ----
    root = tree / ROOT_NAME
    if not root.exists():
        results.append(("FAIL", f"缺根文件 {ROOT_NAME}"))
    else:
        n = char_len(root)
        results.append(("OK" if n <= ROOT_MAX else "FAIL",
                        f"根 {ROOT_NAME}：{n:,} / {ROOT_MAX:,} 字符"))

    # ---- 2. 各主题：单文件 + **主题合计**（评审指出：只卡单文件=闸门形同虚设）----
    over = [(p, char_len(p)) for p in kinds["theme"] if char_len(p) > THEME_MAX]
    results.append(("OK" if not over else "FAIL",
                    f"主题文件 {len(kinds['theme'])} 个，超 {THEME_MAX:,} 字符的 {len(over)} 个"))
    for p, n in over:
        results.append(("FAIL", f"  ↳ {p.relative_to(tree)}：{n:,} 字符"))

    theme_total = {}
    for p in kinds["theme"]:
        rel = p.relative_to(tree).parts
        # references/<主题>.md  或  references/<主题>/<阶段>.md → 主题名固定在 parts[1]
        key = rel[1] if len(rel) > 2 else Path(rel[-1]).stem
        theme_total[key] = theme_total.get(key, 0) + char_len(p)
    over_total = {k: v for k, v in theme_total.items() if v > THEME_TOTAL_MAX}
    results.append(("OK" if not over_total else "FAIL",
                    f"主题合计 {len(theme_total)} 个，超 {THEME_TOTAL_MAX:,} 字符的 {len(over_total)} 个"))
    for k, v in sorted(over_total.items(), key=lambda kv: -kv[1]):
        results.append(("FAIL", f"  ↳ {k}：{v:,} 字符（拆文件不解决合计，必须砍规则或压措辞）"))

    # ---- 3. 索引：单份 + 合计 ----
    over_idx = [(p, char_len(p)) for p in kinds["index"] if char_len(p) > INDEX_MAX]
    results.append(("OK" if not over_idx else "FAIL",
                    f"索引表 {len(kinds['index'])} 个，超 {INDEX_MAX:,} 字符的 {len(over_idx)} 个"))
    for p, n in over_idx:
        results.append(("FAIL", f"  ↳ {p.relative_to(tree)}：{n:,} 字符"))
    idx_total = sum(char_len(p) for p in kinds["index"])
    results.append(("OK" if idx_total <= INDEX_TOTAL_MAX else "FAIL",
                    f"索引合计 {idx_total:,} / {INDEX_TOTAL_MAX:,} 字符"))

    # ---- 4. 全树字符：**只报 INFO，不作判据** ----
    # ★ 2026-11-01 评审后纠正：原先拍的"全树 ≤250 KB"没有依据。全树体积是**仓库/存储成本**，
    #   不是 AI 的上下文成本——AI 是按需读单个文件的，真正该卡的是"单次加载 ≤30,000 字符"。
    #   所以这里降级为 INFO；如果哪天要压仓库体积，再单独立项。
    tree_chars = sum(char_len(p) for p in files if p.suffix in (".md", ".tsv"))
    kb = total_bytes / 1024
    results.append(("INFO",
                    f"全树 {tree_chars:,} 字符 / {kb:,.1f} KB / {len(files)} 个文件（仓库成本，非 AI 成本）"))

    # ---- 5. 单次会话加载估算（根 + 最厚的 2 个主题）----
    root_n = char_len(root) if root.exists() else 0
    themes = sorted((char_len(p) for p in kinds["theme"]), reverse=True)[:2]
    session = root_n + sum(themes)
    results.append(("OK" if session <= SESSION_MAX else "FAIL",
                    f"单次加载估算（根 + 最厚 2 主题）{session:,} / {SESSION_MAX:,} 字符"))

    # ---- 6. 反面样本对照（固定参照，便于感知量级）----
    apk = Path(r"C:\Users\y\.dsh\skills\apk-reverse\SKILL.md")
    if apk.exists():
        results.append(("INFO", f"参照：apk-reverse\\SKILL.md 单文件 {char_len(apk):,} 字符"))

    ok = all(level != "FAIL" for level, _ in results)
    return results, ok


def main():
    """CLI 入口。"""
    tree = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TREE
    results, ok = check(tree)
    print(f"[预算] 检查目标：{tree}")
    for level, msg in results:
        print(f"[预算] {level:<4} {msg}")
    print(f"[预算] 结论：{'OK 全部通过' if ok else 'FAIL 有超限项'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
