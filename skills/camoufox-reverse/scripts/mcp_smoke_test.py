#!/usr/bin/env python3
"""End-to-end smoke test for the camoufox-reverse MCP server.

It speaks real MCP over stdio to the exact server entry point the DSH profile
spawns, so a pass here means the whole chain works: venv -> MCP server -> Camoufox
-> browser.

    .venv\\Scripts\\python.exe bin\\mcp_smoke_test.py
        connect, list tools, run check_environment

    .venv\\Scripts\\python.exe bin\\mcp_smoke_test.py --browser
        also launch the browser (headed), open example.com, take a snapshot

    .venv\\Scripts\\python.exe bin\\mcp_smoke_test.py --browser --headless
        same, but with headless=True (used to probe the Windows headless crash)

    .venv\\Scripts\\python.exe bin\\mcp_smoke_test.py --browser --reverse
        launch the custom reverse build with engine tracing enabled
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVERSE_SELECTOR = "whitenightshadow/152.0.4-beta.30-reverse.5"


def _utf8_console() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _text(result) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts) if parts else repr(result)


def _brief(payload: str, limit: int = 4000) -> str:
    try:
        data = json.loads(payload)
    except Exception:
        return payload[:limit]
    return json.dumps(data, indent=2, ensure_ascii=False)[:limit]


async def run(args) -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "camoufox_reverse_mcp", "--locale", args.locale],
        env=env,
        cwd=str(ROOT),
    )

    print("=" * 78)
    print(f" 启动 MCP server : {sys.executable} -m camoufox_reverse_mcp --locale {args.locale}")
    print("=" * 78)

    failures = 0
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=90)
            tools = await asyncio.wait_for(session.list_tools(), timeout=60)
            names = [tool.name for tool in tools.tools]
            print(f"[ OK ] MCP 握手成功，暴露 {len(names)} 个工具")
            for probe in ("check_environment", "launch_browser", "import_state",
                          "instrumentation", "trace_property_access", "verify_signer_offline"):
                mark = "OK  " if probe in names else "MISS"
                print(f"       [{mark}] {probe}")

            print("-" * 78)
            print(" check_environment")
            env_result = await asyncio.wait_for(
                session.call_tool("check_environment", {}), timeout=120
            )
            print(_brief(_text(env_result)))

            if not args.browser:
                return failures

            print("-" * 78)
            print(f" launch_browser(headless={args.headless}, reverse={args.reverse})")
            launch_args: dict = {"headless": args.headless, "locale": args.locale}
            if args.reverse:
                launch_args.update(browser_version=REVERSE_SELECTOR, enable_trace=True)
            launch = await asyncio.wait_for(
                session.call_tool("launch_browser", launch_args), timeout=300
            )
            launch_text = _text(launch)
            print(_brief(launch_text))
            low = launch_text.lower()
            if any(word in low for word in ("error", "traceback", "breakpoint", "0x80000003", "exit code")):
                failures += 1
                print("   -> 启动结果里出现错误字样，判为失败")

            if "error" not in low:
                print("-" * 78)
                print(" navigate -> take_snapshot")
                nav = await asyncio.wait_for(
                    session.call_tool("navigate", {"url": "https://example.com"}), timeout=180
                )
                print("   navigate:", _brief(_text(nav), 600))
                snap = await asyncio.wait_for(
                    session.call_tool("take_snapshot", {}), timeout=120
                )
                print("   snapshot:", _brief(_text(snap), 900))

                print("-" * 78)
                print(" take_screenshot (base64 文本，仅看长度)")
                shot = await asyncio.wait_for(
                    session.call_tool("take_screenshot", {}), timeout=120
                )
                print(f"   screenshot payload 长度: {len(_text(shot))}")

            print("-" * 78)
            close = await asyncio.wait_for(session.call_tool("close_browser", {}), timeout=120)
            print(" close_browser:", _brief(_text(close), 400))

    return failures


def main() -> int:
    _utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true", help="also launch the browser and navigate")
    parser.add_argument("--headless", action="store_true", help="launch with headless=True instead of headed")
    parser.add_argument("--reverse", action="store_true", help="launch the custom reverse build with tracing")
    parser.add_argument("--locale", default="zh-CN", help="browser locale (default: zh-CN)")
    args = parser.parse_args()

    try:
        failures = asyncio.run(run(args))
    except Exception as error:  # noqa: BLE001
        print(f"[FAIL] 冒烟测试异常：{type(error).__name__}: {error}")
        return 1

    print("=" * 78)
    print(" 结果：通过" if not failures else f" 结果：{failures} 处失败")
    print("=" * 78)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
