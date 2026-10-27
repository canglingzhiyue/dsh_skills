#!/usr/bin/env python
"""沉淀探针发现 —— 把 probe_env.py 的输出转化为可复用的环境补丁。

用法：
    # 从探针输出生成站点档案补丁
    python scripts\harvest.py --site mysite --probe-output probe.json

    # 交互式确认后写入
    python scripts\harvest.py --site mysite --probe-output probe.json --interactive

    # 生成 polyfill 骨架
    python scripts\harvest.py --new-polyfill myfeature --symptom "window.myFeature is not defined"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = SKILL_DIR / "env"
SITE_DIR = ENV_DIR / "sites"
POLYFILL_DIR = ENV_DIR / "polyfills"

sys.path.insert(0, str(ENV_DIR))
import _envlib  # noqa: E402


def load_probe_output(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def suggest_polyfill_name(miss_name: str) -> str:
    """从缺口名建议 polyfill 文件名。"""
    # 清理特殊字符，转 snake_case
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", miss_name)
    clean = re.sub(r"([a-z])([A-Z])", r"\1_\2", clean).lower()
    return f"{clean}_polyfill.js"


def analyze_misses(misses: dict) -> list[dict]:
    """分析缺口，分类建议。"""
    suggestions = []

    for name, count in sorted(misses.items(), key=lambda x: -x[1]):
        # 跳过嵌套访问（如 AAA.foo），只处理根
        if "." in name:
            continue

        suggestion = {
            "name": name,
            "count": count,
            "category": "unknown",
            "action": "manual",
            "detail": "",
        }

        # 分类
        lower = name.lower()
        if any(k in lower for k in ["md5", "sha", "encrypt", "decrypt", "sign", "crypto"]):
            suggestion["category"] = "crypto"
            suggestion["action"] = "check_iv8_builtin"
            suggestion["detail"] = "iv8 内置 SubtleCrypto，先确认是否满足"
        elif any(k in lower for k in ["cookie", "token", "session"]):
            suggestion["category"] = "credential"
            suggestion["action"] = "manual"
            suggestion["detail"] = "通常是服务端下发，不要伪造"
        elif any(k in lower for k in ["akamai", "bmak", "sensor"]):
            suggestion["category"] = "antibot"
            suggestion["action"] = "use_polyfill"
            suggestion["detail"] = "可尝试 akamai_surface.js"
        elif any(k in lower for k in ["channel", "worker", "socket"]):
            suggestion["category"] = "api"
            suggestion["action"] = "check_iv8_version"
            suggestion["detail"] = "可能是 iv8 版本过老，0.1.4 已内置很多"
        elif name.startswith("$") or name in ["jQuery", "_"]:
            suggestion["category"] = "library"
            suggestion["action"] = "load_real_lib"
            suggestion["detail"] = "加载真实库文件，不要模拟"

        suggestions.append(suggestion)

    return suggestions


def generate_polyfill_skeleton(name: str, symptom: str) -> str:
    """生成 polyfill 骨架代码。"""
    return f'''/* {name} polyfill
 *
 * 症状：{symptom}
 * 生成时间：{datetime.now().strftime("%Y-%m-%d")}
 *
 * TODO：实现具体逻辑
 */
(function () {{
  if (typeof window.{name} !== "undefined") {{
    return; // 已存在，不覆盖
  }}

  // TODO：实现 {name}
  window.{name} = {{
    // 示例属性
    // method: function() {{ ... }}
  }};
}})();
'''


def update_manifest(polyfill_id: str, filename: str, symptom: str, tags: list[str] | None = None):
    """更新 manifest.json。"""
    mf_path = POLYFILL_DIR / "manifest.json"
    if mf_path.exists():
        mf = json.loads(mf_path.read_text(encoding="utf-8"))
    else:
        mf = {"_comment": "缺失 API 补丁索引", "_schema": {}, "polyfills": []}

    # 检查是否已存在
    for item in mf.get("polyfills", []):
        if item["id"] == polyfill_id:
            print(f"  [跳过] {polyfill_id} 已存在于 manifest")
            return

    mf.setdefault("polyfills", []).append({
        "id": polyfill_id,
        "file": filename,
        "symptom": symptom,
        "tags": tags or [],
        "sites": [],
        "always": False,
        "note": "由 harvest.py 自动生成，需人工验证",
        "added": datetime.now().strftime("%Y-%m-%d"),
    })

    mf_path.write_text(json.dumps(mf, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [写入] manifest.json 新增 {polyfill_id}")


def update_site_profile(site: str, suggestions: list[dict], interactive: bool = False):
    """更新站点档案。"""
    site_file = SITE_DIR / f"{site}.yml"
    if not site_file.exists():
        print(f"  [错误] 站点档案不存在: {site_file}")
        print(f"  请先运行: python scripts\\new_site.py --name {site}")
        return

    content = site_file.read_text(encoding="utf-8")

    # 找 polyfills 部分
    if "polyfills:" not in content:
        content += "\npolyfills:\n"

    # 添加建议
    added = []
    for s in suggestions:
        if s["action"] == "use_polyfill":
            polyfill_id = f"{s['name'].lower()}_polyfill"
            if polyfill_id not in content:
                content += f"  - {polyfill_id}\n"
                added.append(polyfill_id)

    if added:
        site_file.write_text(content, encoding="utf-8")
        print(f"  [更新] {site}.yml 添加 polyfills: {', '.join(added)}")
    else:
        print(f"  [无变化] {site}.yml 无需更新")


def main() -> int:
    ap = argparse.ArgumentParser(description="沉淀探针发现")
    ap.add_argument("--site", help="站点档案名")
    ap.add_argument("--probe-output", help="probe_env.py 的 JSON 输出文件")
    ap.add_argument("--interactive", action="store_true", help="交互式确认")
    ap.add_argument("--new-polyfill", help="直接创建新 polyfill")
    ap.add_argument("--symptom", help="polyfill 对应症状描述")
    args = ap.parse_args()

    if args.new_polyfill:
        if not args.symptom:
            print("错误：--new-polyfill 需要同时提供 --symptom")
            return 1

        filename = f"{args.new_polyfill}.js"
        filepath = POLYFILL_DIR / filename
        filepath.write_text(generate_polyfill_skeleton(args.new_polyfill, args.symptom), encoding="utf-8")
        print(f"[创建] {filepath}")

        update_manifest(args.new_polyfill, filename, args.symptom)
        return 0

    if not args.probe_output:
        print("错误：需要 --probe-output 指定探针输出文件")
        return 1

    # 加载探针输出
    probe_data = load_probe_output(args.probe_output)
    misses = probe_data.get("misses", {})

    if not misses:
        print("探针未发现缺口，无需沉淀")
        return 0

    # 分析
    suggestions = analyze_misses(misses)

    print("=" * 70)
    print("探针发现分析")
    print("=" * 70)

    for s in suggestions:
        print(f"\n[{s['category']:10s}] {s['name']} (被访问 {s['count']} 次)")
        print(f"  建议: {s['action']}")
        print(f"  说明: {s['detail']}")

        if args.interactive:
            resp = input(f"  是否为此创建 polyfill? [y/N] ")
            if resp.lower() == "y":
                filename = suggest_polyfill_name(s["name"])
                filepath = POLYFILL_DIR / filename
                filepath.write_text(generate_polyfill_skeleton(s["name"], f"window.{s['name']} is not defined"), encoding="utf-8")
                update_manifest(s["name"].lower(), filename, f"window.{s['name']} is not defined", tags=[s["category"]])
                print(f"    [创建] {filename}")

    # 更新站点档案
    if args.site:
        update_site_profile(args.site, suggestions, args.interactive)

    print("\n" + "=" * 70)
    print("下一步：")
    print("1. 实现生成的 polyfill 骨架")
    print("2. 运行 iv8_run.py 验证")
    print("3. 确认有效后更新站点档案的 pitfalls")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
