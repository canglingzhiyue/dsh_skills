#!/usr/bin/env python3
"""Warm the Camoufox cache so the first MCP `launch_browser` is clean.

Why this is required
--------------------
On its first launch Camoufox downloads its default addon (uBlock Origin) and
prints a progress line to **stdout**:

    \\rDownloading addon (UBO)...\\rExtracting addon (UBO): Complete\\r

Inside an MCP stdio session stdout carries the JSON-RPC stream, so that line
corrupts the framing and the client reports:

    Failed to parse JSONRPC message from server ... Invalid JSON

Running this script once (outside MCP) downloads and caches the addon, after
which `launch_browser` starts silently. Re-run it whenever the cache is cleared,
Camoufox is upgraded, or an MCP client starts reporting JSON-RPC parse errors.

    .venv\\Scripts\\python.exe bin\\warmup.py
"""

from __future__ import annotations

import sys

ROOT_MARKER = "camoufox-reverse"


def _utf8_console() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main() -> int:
    _utf8_console()
    print("预热 Camoufox 缓存（下载默认插件 + 验证浏览器可启动）...")
    print("会短暂弹出一个浏览器窗口，属正常现象。")

    try:
        from camoufox.sync_api import Camoufox
    except Exception as error:  # noqa: BLE001
        print(f"[FAIL] 无法导入 camoufox：{error}")
        return 1

    try:
        with Camoufox(headless=False, locale="zh-CN") as browser:
            page = browser.new_page()
            page.goto("about:blank", timeout=60_000)
            print("[ OK ] 浏览器已启动（引擎可用，插件已缓存）")
    except Exception as error:  # noqa: BLE001
        print(f"[FAIL] 启动失败：{type(error).__name__}: {error}")
        return 1

    print("[完成] 现在可以在 DSH 里正常调用 mcp__camoufox__launch_browser 了。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
