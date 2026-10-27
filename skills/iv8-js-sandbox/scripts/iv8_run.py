#!/usr/bin/env python
"""iv8 统一运行入口 —— 加载环境库后执行目标 JS。

用法：
    # 直接跑一段 JS
    python iv8_run.py -e "1 + 2"

    # 跑目标 JS 文件，加载某站点档案
    python iv8_run.py -f target.js --site akamai

    # 跑 JS 并取回某个表达式的结果
    python iv8_run.py -f target.js --site douyin --eval "window.result"

    # 只看最终环境的差异（不执行目标 JS）
    python iv8_run.py --site akamai --show-env

设计要点：
    环境库按 base < polyfill < site < 显式覆盖 的顺序叠加，
    所有叠加结果都会打印出来（--quiet 可关），
    这样"这次到底补了什么"永远是可见的，不会变成玄学。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ENV_DIR = Path(__file__).resolve().parent.parent / "env"
sys.path.insert(0, str(ENV_DIR))

import _envlib  # noqa: E402
import iv8  # noqa: E402


def build_context(args):
    env = _envlib.build_environment(site=args.site)

    ctx_kwargs = {}
    if env:
        ctx_kwargs["environment"] = env

    # 站点档案里的运行时策略
    site_cfg = _envlib.load_site(args.site) if args.site else {}
    runtime = site_cfg.get("runtime", {}) if isinstance(site_cfg, dict) else {}

    time_mode = args.time_mode or runtime.get("time_mode") or "logical"
    ctx_kwargs["time_mode"] = time_mode

    if args.debug:
        ctx_kwargs["mode"] = "debug"

    return ctx_kwargs, env, runtime


def inject_polyfills(ctx, site, tags, quiet=False):
    items = _envlib.select_polyfills(site=site, tags=tags)
    for item in items:
        src = _envlib.polyfill_source(item)
        ctx.eval(src)
        if not quiet:
            print(f"[polyfill] 已注入 {item['id']} ({item['file']})", file=sys.stderr)
    return [i["id"] for i in items]


def main() -> int:
    ap = argparse.ArgumentParser(description="iv8 环境库运行入口")
    ap.add_argument("-f", "--file", help="要执行的 JS 文件")
    ap.add_argument("-e", "--expr", help="直接执行的 JS 表达式")
    ap.add_argument("--site", help="站点档案名（env/sites/<name>.yml）")
    ap.add_argument("--tag", action="append", default=[], help="额外加载的 polyfill 标签，可重复")
    ap.add_argument("--eval", dest="post_eval", help="执行完后再求值的 JS 表达式")
    ap.add_argument("--time-mode", choices=["logical", "system"], help="覆盖时间模式")
    ap.add_argument("--debug", action="store_true", help="debug 模式（启用 API 监控）")
    ap.add_argument("--show-env", action="store_true", help="只打印最终环境并退出")
    ap.add_argument("--quiet", action="store_true", help="不打印叠加过程")
    args = ap.parse_args()

    ctx_kwargs, env, runtime = build_context(args)

    if args.show_env:
        print(json.dumps(env, ensure_ascii=False, indent=2))
        return 0

    if not args.file and not args.expr:
        ap.error("需要 -f <js文件> 或 -e <表达式> 之一")

    if not args.quiet:
        print(f"[env] 站点档案: {args.site or '(无)'}", file=sys.stderr)
        print(f"[env] time_mode: {ctx_kwargs.get('time_mode')}", file=sys.stderr)
        print(f"[env] environment 覆盖层数: {_count_layers(env)} 个顶层键", file=sys.stderr)
        if runtime.get("needs_real_network"):
            print("[env] 注意：该站点需要真实网络往返（社区版无内置网络栈）", file=sys.stderr)

    with iv8.JSContext(**ctx_kwargs) as ctx:
        inject_polyfills(ctx, args.site, args.tag, quiet=args.quiet)

        if args.file:
            src = Path(args.file).read_text(encoding="utf-8")
            result = ctx.eval(src)
            if not args.quiet:
                print(f"[run] 已执行 {args.file} ({len(src)} 字符)", file=sys.stderr)
        else:
            result = ctx.eval(args.expr)

        if result is not None:
            print(json.dumps(result, ensure_ascii=False, default=str))

        if args.post_eval:
            out = ctx.eval(args.post_eval, to_py=True)
            print(json.dumps(out, ensure_ascii=False, default=str))

    return 0


def _count_layers(env) -> int:
    return len(env) if isinstance(env, dict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
