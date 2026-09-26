#!/usr/bin/env python3
"""Open a visible Camoufox window so a human can log in, then save the session.

Why this exists
---------------
camoufox-reverse-mcp has no persistent-profile support: its `launch_browser`
always builds a fresh, randomly fingerprinted browser, and the only way to
carry a login across runs is the `export_state` / `import_state` tool pair. A
QR-code or SMS login needs a human in front of a real window, which is exactly
what this script provides.

Two modes
---------
default        A normal browser session. After you confirm the login, cookies and
               localStorage are written to  states/<name>.json  — hand that path
               to the MCP tool `import_state` in your next session.

--persistent   A persistent profile under  profiles/<name>/  instead, which keeps
               cookies, localStorage, IndexedDB, caches and service workers
               across runs. The storage state is exported as well, so you can
               still drive camoufox-reverse-mcp with `import_state`. Use this
               when a site keeps its login in IndexedDB and the plain export
               keeps logging you out.

The window stays open until you press Enter here, so log in at your own pace.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = ROOT / "states"
PROFILES_DIR = ROOT / "profiles"


def _utf8_console() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open a visible Camoufox window, log in by hand, save the session.",
    )
    parser.add_argument("--url", required=True, help="page to open for the manual login")
    parser.add_argument(
        "--name",
        required=True,
        help="short label for this site; used for states/<name>.json and profiles/<name>/",
    )
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="keep a full persistent profile (cookies + localStorage + IndexedDB + caches)",
    )
    parser.add_argument("--locale", default="zh-CN", help="browser locale (default: zh-CN)")
    parser.add_argument("--proxy", default=None, help="proxy URL, e.g. http://127.0.0.1:7890")
    parser.add_argument("--geoip", action="store_true", help="derive locale/timezone from the proxy exit IP")
    parser.add_argument("--os", dest="os_name", default="auto", help="OS fingerprint to emulate (default: auto)")
    parser.add_argument("--no-humanize", action="store_true", help="disable humanized mouse movement")
    return parser


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    args = build_parser().parse_args(argv)

    STATES_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATES_DIR / f"{args.name}.json"
    profile_dir = PROFILES_DIR / args.name

    from camoufox.sync_api import Camoufox

    options: dict = {
        "headless": False,
        "locale": args.locale,
        "os": args.os_name,
        "humanize": not args.no_humanize,
    }
    if args.geoip:
        options["geoip"] = True
    if args.proxy:
        options["proxy"] = {"server": args.proxy}

    if args.persistent:
        options.update(persistent_context=True, user_data_dir=str(profile_dir))

    print("=" * 72)
    print(f"  站点标识 : {args.name}")
    print(f"  打开地址 : {args.url}")
    print(f"  登录态   : {state_path}")
    if args.persistent:
        print(f"  持久配置 : {profile_dir}")
    print(f"  模式     : {'持久 profile' if args.persistent else '一次性会话（导出 state）'}")
    print("=" * 72)
    print("浏览器窗口即将打开。请在其中完成扫码 / 短信 / 密码登录，")
    print("确认已进入登录后的页面，然后回到本窗口按回车保存登录态。")
    print()

    with Camoufox(**options) as instance:
        if args.persistent:
            context = instance
            page = context.pages[0] if context.pages else context.new_page()
        else:
            context = instance.new_context()
            page = context.new_page()

        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as error:  # noqa: BLE001 - report and let the human continue
            print(f"[提示] 打开 {args.url} 出错：{error}")
            print("[提示] 窗口仍然可用，你可以手动导航到登录页。")

        input(">>> 登录完成后，在本窗口按回车保存登录态... ")

        try:
            context.storage_state(path=str(state_path))
        except Exception as error:  # noqa: BLE001
            print(f"[错误] 导出登录态失败：{error}")
            return 1

    print()
    print(f"[完成] 登录态已保存：{state_path}")
    print()
    print("在 DSH 会话里让 MCP 复用它（每次 launch_browser 之后都要调一次）：")
    print(f'  1) mcp__camoufox__launch_browser')
    print(f'  2) mcp__camoufox__import_state(state_path=r"{state_path}")')
    print(f'  3) mcp__camoufox__navigate(url="<目标页>")')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
