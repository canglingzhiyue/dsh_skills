#!/usr/bin/env python3
"""One-screen health check for this Camoufox reverse-engineering setup.

Run it from the console menu, or directly:
    .venv\\Scripts\\python.exe bin\\check_env.py
"""

from __future__ import annotations

import importlib.metadata as md
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OK = "[ OK ]"
WARN = "[WARN]"
BAD = "[FAIL]"


def _utf8_console() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _version(package: str) -> str | None:
    try:
        return md.version(package)
    except Exception:
        return None


def _line(status: str, label: str, detail: str = "") -> None:
    print(f"{status} {label:<26} {detail}")


def main() -> int:
    _utf8_console()
    problems = 0

    print("=" * 78)
    print(" Camoufox 逆向环境自检")
    print("=" * 78)
    _line(OK, "工作区", str(ROOT))
    _line(OK, "Python", f"{sys.version.split()[0]}  ({sys.executable})")

    print("-" * 78)
    print(" Python 依赖")
    expected = {
        "camoufox": "引擎封装（浏览器启动 / 指纹）",
        "playwright": "必须 <1.63（camoufox 的上界）",
        "camoufox-reverse-mcp": "MCP server 本体",
        "mcp": "MCP Python SDK",
        "browserforge": "指纹生成",
        "geoip2": "代理地理推断（--geoip 需要）",
        "esprima": "JS 解析回退",
    }
    versions: dict[str, str | None] = {}
    for package, note in expected.items():
        version = _version(package)
        versions[package] = version
        if version is None:
            status = WARN if package in {"geoip2", "esprima"} else BAD
            if status == BAD:
                problems += 1
            _line(status, package, f"未安装 — {note}")
        else:
            _line(OK, package, f"{version} — {note}")

    playwright = versions.get("playwright")
    if playwright:
        major, minor = (int(x) for x in playwright.split(".")[:2])
        if (major, minor) >= (1, 63):
            problems += 1
            _line(BAD, "playwright 版本窗口", f"{playwright} 超出 camoufox 的 <1.63 上界")

    print("-" * 78)
    print(" 浏览器引擎")
    try:
        from camoufox.pkgman import INSTALL_DIR
        from camoufox.multiversion import BROWSERS_DIR, get_active_path

        _line(OK, "缓存目录", str(INSTALL_DIR))
        if not INSTALL_DIR.exists():
            problems += 1
            _line(BAD, "缓存状态", "目录不存在，尚未安装任何浏览器")
            return _summary(problems)

        active = None
        try:
            active = get_active_path()
        except Exception:
            active = None
        _line(OK if active else BAD, "active 浏览器", str(active) if active else "未设置（先跑菜单里的安装/或 camoufox fetch）")
        if not active:
            problems += 1

        found_any = False
        if BROWSERS_DIR.exists():
            for repo_dir in sorted(BROWSERS_DIR.iterdir()):
                if not repo_dir.is_dir():
                    continue
                builds = sorted(p.name for p in repo_dir.iterdir() if p.is_dir())
                for build in builds:
                    found_any = True
                    tag = "定制版（含 77 点引擎追踪）" if repo_dir.name == "whitenightshadow" else "官方版"
                    _line(OK, f"{repo_dir.name}", f"{build}   {tag}")
        if not found_any:
            problems += 1
            _line(BAD, "已安装浏览器", "一个都没有")

        reverse = list(BROWSERS_DIR.glob("whitenightshadow/*")) if BROWSERS_DIR.exists() else []
        if reverse:
            selector = f"whitenightshadow/{reverse[0].name}"
            _line(OK, "trace_property_access", f"可用（selector: {selector}）")
        else:
            _line(WARN, "trace_property_access", "不可用 — 未安装定制版浏览器")
    except Exception as error:  # noqa: BLE001
        problems += 1
        _line(BAD, "引擎检查", f"异常：{error}")

    print("-" * 78)
    print(" 辅助工具")
    node = shutil.which("node")
    if node:
        _line(OK, "node", node)
        acorn = ROOT / "camoufox-reverse-mcp" / "src" / "camoufox_reverse_mcp" / "vendor" / "acorn.cjs"
        _line(OK if acorn.exists() else WARN, "vendor/acorn.cjs", "存在（现代 JS 语法解析）" if acorn.exists() else "缺失")
    else:
        _line(WARN, "node", "未找到 — verify_signer_offline(runtime='node') 不可用，会回退 esprima")

    state_dir = ROOT / "states"
    saved = sorted(p.stem for p in state_dir.glob("*.json")) if state_dir.exists() else []
    _line(OK if saved else WARN, "已保存登录态", ", ".join(saved) if saved else "暂无（用菜单第 2 项登录）")

    return _summary(problems)


def _summary(problems: int) -> int:
    print("=" * 78)
    if problems:
        print(f" 结果：发现 {problems} 个问题（见上面的 [FAIL]）")
    else:
        print(" 结果：全部就绪")
    print("=" * 78)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
