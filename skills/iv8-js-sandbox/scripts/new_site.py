#!/usr/bin/env python
"""新建站点档案 —— 交互式或命令行创建 env/sites/<name>.yml。

用法：
    # 交互式
    python scripts\new_site.py

    # 命令行
    python scripts\new_site.py --name mysite --url https://example.com --kind 电商
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = SKILL_DIR / "env" / "sites"

TEMPLATE = '''# {name} 站点档案
# 创建时间：{date}
# 创建者：iv8-js-sandbox new_site.py

name: {name}
url: {url}
kind: {kind}
tags: [{tags}]

# 只写该站特有的差异，通用的进 base.py
# 查看可配置项：python -c "import iv8; print(iv8.JSContext.get_defaults())"
environment:
  navigator:
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    # 版本号必须与该站实际下发的资源匹配
    # platform: Win32
    # language: zh-CN
  # screen:
  #   width: 1920
  #   height: 1080
  # location:
  #   href: {url}

# 需要加载的 polyfill
polyfills: []

# 运行时策略
runtime:
  time_mode: logical       # logical=快速，system=真实时间（POW/时序敏感用）
  needs_real_network: false
  # warmup_rounds: 0

# 已知坑（重要！逆向过程中遇到就记录）
pitfalls:
  - "TODO: 记录该站的坑"

# 探针额外目标（该站特有的探测点）
extra_probe_targets: []

# 备注
notes: |
  TODO: 记录逆向过程中的关键发现
'''


def create_site(name: str, url: str, kind: str, tags: list[str]) -> Path:
    """创建站点档案。"""
    site_file = SITE_DIR / f"{name}.yml"

    if site_file.exists():
        print(f"[警告] 站点档案已存在: {site_file}")
        resp = input("覆盖? [y/N] ")
        if resp.lower() != "y":
            print("取消")
            sys.exit(0)

    content = TEMPLATE.format(
        name=name,
        url=url or "https://example.com",
        kind=kind or "未分类",
        tags=", ".join(tags) if tags else "",
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    site_file.write_text(content, encoding="utf-8")
    print(f"[创建] {site_file}")

    return site_file


def interactive():
    """交互式创建。"""
    print("=" * 50)
    print("新建站点档案")
    print("=" * 50)

    name = input("站点名（英文，如 douyin）: ").strip()
    if not name:
        print("错误：站点名不能为空")
        sys.exit(1)

    url = input("站点 URL: ").strip()
    kind = input("类型（电商/政务/内容平台/其他）: ").strip() or "未分类"
    tags_input = input("标签（逗号分隔，如 akamai,签名）: ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    create_site(name, url, kind, tags)

    print("\n" + "=" * 50)
    print("下一步：")
    print(f"1. 编辑 env/sites/{name}.yml，补充 environment 和 pitfalls")
    print(f"2. 运行探针: python scripts\\probe_env.py -f target.js --site {name}")
    print(f"3. 运行: python scripts\\iv8_run.py -f target.js --site {name}")
    print("=" * 50)


def main() -> int:
    ap = argparse.ArgumentParser(description="新建站点档案")
    ap.add_argument("--name", help="站点名")
    ap.add_argument("--url", help="站点 URL")
    ap.add_argument("--kind", help="站点类型")
    ap.add_argument("--tags", help="标签，逗号分隔")
    ap.add_argument("--list", action="store_true", help="列出现有站点")
    args = ap.parse_args()

    if args.list:
        sites = list(SITE_DIR.glob("*.yml"))
        if sites:
            print("现有站点档案：")
            for s in sorted(sites):
                print(f"  {s.stem}")
        else:
            print("暂无站点档案")
        return 0

    if args.name:
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        create_site(args.name, args.url or "", args.kind or "未分类", tags)
    else:
        interactive()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
