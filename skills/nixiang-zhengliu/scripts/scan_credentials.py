"""scan_credentials.py —— 活凭据扫描（派发 subagent / 外发前的脱敏体检）。

只扫**活凭据**，不扫技术常量。这条界线是硬规矩（plan.md §三）：
    ✅ 要报：Cookie / Bearer token / 私钥 / 会话 token / 真实手机号 / 内网 IP / 邮箱
    ❌ 不报：算法盐值（`SALT = "2ddb…"`）、密钥常量、密文样例、签名原文、MD5 输入串
       —— 这些是算法还原笔记的全部价值，脱掉等于删掉技术事实。

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\scan_credentials.py

输出：`data\\anchors\\脱敏体检.md`（按风险类型分组，逐条给出 文件:行号 + 命中片段）。
    本脚本**只报不改**：要不要遮、遮哪一段，由人决定。

关键结论 / 限制：
    - 命中≠泄露：测试号 `13300000000`、示例 `Cookie: uid=<payload>` 也会命中，属正常误报。
    - 【未验证】模式表是按两库文风设计的，换语料库要复核一遍。
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import common

OUT = common.DATA_DIR / "anchors" / "脱敏体检.md"

# 风险类型 → (正则, 说明)
PATTERNS = [
    ("私钥", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "真实私钥块"),
    ("Cookie头", re.compile(r"(?:Set-)?Cookie:\s*[^\n]{16,}"), "完整 Cookie 头"),
    ("Bearer/token", re.compile(r"(?:Bearer|Authorization)\s+[A-Za-z0-9\-_.=+/]{16,}"),
     "访问令牌"),
    ("会话token", re.compile(r"(?:passport_token|SESSDATA|sessionid|csrftoken|access_token)"
                          r"\s*[=:]\s*[A-Za-z0-9\-_.=+/]{12,}"), "会话级令牌"),
    ("内网IP", re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}"
                       r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"), "内网地址"),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "真实或测试手机号"),
    ("邮箱", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}"), "邮箱"),
]

SKIP_NAMES = {"INDEX.md"}
MAX_PER_TYPE = 60         # 每类最多列多少条，避免报告过长


def scan_file(path: Path):
    """扫一个文件，返回 [(类型, 行号, 片段)]。"""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    hits = []
    for no, ln in enumerate(lines, start=1):
        if len(ln) > 400:                 # 表格/长行里多为拼接内容，跳过噪声
            continue
        for kind, rx, _desc in PATTERNS:
            m = rx.search(ln)
            if m:
                frag = m.group(0).strip()
                hits.append((kind, no, frag[:100]))
                break                     # 一行只报一次，按 PATTERNS 优先级
    return hits


def run():
    """扫两库笔记，写体检报告。"""
    per_type = Counter()
    rows = {kind: [] for kind, _r, _d in PATTERNS}
    files_scanned = 0
    for notes_dir, platform in ((common.NOTES_52PJ, common.P_52PJ), (common.NOTES_KX, common.P_KX)):
        for p in sorted(notes_dir.glob("*.md")):
            if p.name in SKIP_NAMES:
                continue
            files_scanned += 1
            for kind, no, frag in scan_file(p):
                per_type[kind] += 1
                if len(rows[kind]) < MAX_PER_TYPE:
                    rows[kind].append((platform, p.name, no, frag))

    lines = [
        "# 脱敏体检报告（只报不改）",
        "",
        f"> scan_credentials.py ｜ 扫 {files_scanned:,} 篇笔记 ｜ 生成 2026-11-01",
        "> **不扫**：算法盐值、密钥常量、密文样例、签名原文、MD5 输入串 —— 这些是技术事实，必须保留。",
        "",
        "## 一、汇总",
        "",
        "| 风险类型 | 命中行数 |",
        "|---|---|",
    ]
    for kind, _rx, desc in PATTERNS:
        lines.append(f"| {kind}（{desc}） | {per_type[kind]:,} |")
    total = sum(per_type.values())
    lines += ["", f"合计 **{total:,}** 处命中。命中≠泄露：测试号与示例串也会命中，需人工过一眼。", ""]
    for kind, _rx, desc in PATTERNS:
        if not rows[kind]:
            continue
        lines += [f"## {kind}（{desc}）", "", "| 平台 | 文件 | 行 | 片段 |", "|---|---|---|---|"]
        for plat, name, no, frag in rows[kind]:
            safe = frag.replace("|", "\\|")
            lines.append(f"| {plat} | {name} | {no} | `{safe}` |")
        lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[脱敏] 扫 {files_scanned:,} 篇｜命中 {total:,} 处｜报告 → {OUT}")
    for kind, _r, _d in PATTERNS:
        print(f"[脱敏]   {kind:<12} {per_type[kind]:,}")
    return total


if __name__ == "__main__":
    run()
