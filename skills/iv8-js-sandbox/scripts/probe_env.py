#!/usr/bin/env python
"""环境探针 —— 自动发现目标 JS 探测了什么、我们缺什么。

这是"成长型"的入口：每逆向一个新站点，先跑它，得到一份差异清单，
把确认有效的差异沉淀进 env/，下次同类站点直接复用，不再重头补。

原理：
    用 `with (Proxy(window))` 包住目标 JS 的执行。Proxy 的 has/get 陷阱
    能记录下 JS 里**每一次全局名字的查找**，以及查找结果是 undefined 的项。
    undefined 的那些，就是候选缺口。

用法：
    # 目标 JS 里跑，列出所有被探测但缺失的全局名
    python probe_env.py -f target.js --site akamai

    # 只看访问频次最高的名字（降噪）
    python probe_env.py -f target.js --top 40

    # 输出可粘贴进站点档案的 YAML 骨架
    python probe_env.py -f target.js --site newsite --emit-profile
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ENV_DIR = Path(__file__).resolve().parent.parent / "env"
sys.path.insert(0, str(ENV_DIR))

import _envlib  # noqa: E402
import iv8  # noqa: E402

# ------------------------------------------------------------------ 探针 JS
#
# 注意：探针是**开发期工具**，会修改 window 上属性的描述符，
# 因此绝不能出现在最终交付的运行链路上 —— 目标 JS 有可能察觉到。
# 它的产物是"清单"，不是"运行环境"。
#
# 技术选型说明：
#   1. defineProperty 方案（当前）：在 window 上为常见探测目标定义 getter，
#      捕获 `window.XXX` 显式访问。可靠、无 Proxy 兼容性问题。
#   2. Proxy + with 方案（备选）：可捕获裸标识符，但在 iv8 0.1.4 中
#      `window.XXX` 访问会错误路由到 Symbol.unscopables，已弃用。
#
# 探测目标来源：
#   - COMMON_PROBE_TARGETS：补环境社区总结的常见反爬/风控探测点
#   - 站点档案里的 extra_probe_targets：站点特有的探测点
#
# 重要限制：
#   本探针只能捕获**预设列表中的属性**。对于"发现新探测点"的需求，
#   应使用 iv8 debug 模式的 API 监控（见 SKILL.md 的调试章节）。
#   本探针的定位是：**验证当前环境是否覆盖了目标 JS 的已知探测点**。
PROBE_JS = r"""
window.__PROBE__ = { gets: {}, misses: {}, errors: [] };

(function () {
  var P = window.__PROBE__;

  // 补环境社区总结的常见探测目标
  var COMMON_TARGETS = [
    // 通用反爬
    "phantom", "callPhantom", "_phantom", "phantomToken",
    "webdriver", "domAutomation", "domAutomationController",
    "spawn", "emit", "Buffer", "process", "global",
    "chrome", "callSelenium", "_Selenium_IDE_Recorder",
    // 厂商特定
    "Akamai", "akamai", "bmak", "_abck", "bm_sz", "sensor_data",
    "MessageChannel", "RTCPeerConnection", "Notification",
    "BatteryManager", "Worker", "SharedWorker", "ServiceWorker",
    "IO", "$", "jQuery", "_",
    // 常见加密/签名函数
    "hex_md5", "md5", "sha1", "sha256", "CryptoJS",
    "encrypt", "decrypt", "sign", "token", "getToken"
  ];

  // 从站点档案注入的额外探测目标
  var EXTRA_TARGETS = window.__EXTRA_PROBE_TARGETS__ || [];

  var allTargets = COMMON_TARGETS.concat(EXTRA_TARGETS);
  var seen = {};

  // 在 window 上定义 getter 来捕获访问
  allTargets.forEach(function (name) {
    if (seen[name]) return;
    seen[name] = true;

    var originalValue;
    var hadOriginal = false;

    try {
      hadOriginal = name in window;
      originalValue = window[name];
    } catch (e) {}

    try {
      Object.defineProperty(window, name, {
        get: function () {
          var isDefined = (typeof originalValue !== "undefined");
          P.gets[name] = (P.gets[name] || 0) + 1;
          if (!isDefined) {
            P.misses[name] = (P.misses[name] || 0) + 1;
            // 返回可链式访问的替身，让目标 JS 继续深入
            var stub = new Proxy(function () {}, {
              get: function (t, k) {
                var n = name + "." + String(k);
                P.gets[n] = (P.gets[n] || 0) + 1;
                P.misses[n] = (P.misses[n] || 0) + 1;
                return stub;
              },
              apply: function () {
                // 记录函数调用
                P.gets[name + "()"] = (P.gets[name + "()"] || 0) + 1;
                return stub;
              },
              construct: function () {
                P.gets["new " + name] = (P.gets["new " + name] || 0) + 1;
                return stub;
              }
            });
            return stub;
          }
          return originalValue;
        },
        set: function (v) {
          originalValue = v;
          hadOriginal = true;
          P.defined = P.defined || [];
          P.defined.push(name);
        },
        configurable: true,
        enumerable: true
      });
    } catch (e) {
      P.errors.push("defineProperty failed for " + name + ": " + e.message);
    }
  });

  // 同时监控 document.cookie 的读取（很多风控从这里读 _abck）
  try {
    var cookieDesc = Object.getOwnPropertyDescriptor(Document.prototype, "cookie") ||
                     Object.getOwnPropertyDescriptor(HTMLDocument.prototype, "cookie");
    if (cookieDesc && cookieDesc.get) {
      Object.defineProperty(document, "cookie", {
        get: function () {
          P.gets["document.cookie"] = (P.gets["document.cookie"] || 0) + 1;
          return cookieDesc.get.call(this);
        },
        configurable: true
      });
    }
  } catch (e) {}

  // 执行目标代码的入口
  window.__PROBE_RUN__ = function (fn) {
    try { return fn(); }
    catch (e) { P.errors.push(String(e && e.message || e)); }
  };
})();
"""


def run_probe(js_file: str | None, expr: str | None, site: str | None,
              tags: list[str], time_mode: str | None) -> dict:
    env = _envlib.build_environment(site=site)
    site_cfg = _envlib.load_site(site) if site else {}
    runtime = site_cfg.get("runtime", {}) if isinstance(site_cfg, dict) else {}

    kwargs: dict = {"time_mode": time_mode or runtime.get("time_mode") or "logical"}
    if env:
        kwargs["environment"] = env

    with iv8.JSContext(**kwargs) as ctx:
        # 先注入 polyfill，探针只报告"补过之后仍然缺"的东西
        for item in _envlib.select_polyfills(site=site, tags=tags):
            ctx.eval(_envlib.polyfill_source(item))

        # 先注入站点档案里的额外探测目标（必须在 PROBE_JS 之前）
        extra_targets = site_cfg.get("extra_probe_targets", []) if isinstance(site_cfg, dict) else []
        if extra_targets:
            targets_js = json.dumps(extra_targets)
            ctx.eval(f"window.__EXTRA_PROBE_TARGETS__ = {targets_js};")

        ctx.eval(PROBE_JS)

        if js_file:
            src = Path(js_file).read_text(encoding="utf-8")
            ctx.eval(f"window.__PROBE_RUN__(function(){{ {src} }});")
        elif expr:
            ctx.eval(f"window.__PROBE_RUN__(function(){{ {expr} }});")

        data = ctx.eval("window.__PROBE__", to_py=True)

    return data or {"gets": {}, "misses": {}, "errors": []}


def main() -> int:
    ap = argparse.ArgumentParser(description="iv8 环境探针")
    ap.add_argument("-f", "--file", help="目标 JS 文件")
    ap.add_argument("-e", "--expr", help="目标 JS 表达式")
    ap.add_argument("--site", help="站点档案名")
    ap.add_argument("--tag", action="append", default=[], help="polyfill 标签")
    ap.add_argument("--top", type=int, default=30, help="每类展示条数")
    ap.add_argument("--time-mode", choices=["logical", "system"])
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    ap.add_argument("--emit-profile", action="store_true",
                    help="输出可粘贴的站点档案 YAML 骨架")
    args = ap.parse_args()

    if not args.file and not args.expr:
        ap.error("需要 -f <js文件> 或 -e <表达式>")

    data = run_probe(args.file, args.expr, args.site, args.tag, args.time_mode)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    gets = Counter(data.get("gets", {}))
    misses = Counter(data.get("misses", {}))
    errors = data.get("errors", [])

    print("=" * 66)
    print(f"探针结果  (站点: {args.site or '无'})")
    print("=" * 66)
    print(f"全局查找总数: {sum(gets.values())}   不同名字: {len(gets)}")
    print(f"其中命中 undefined: {len(misses)} 个名字\n")

    if misses:
        print(f"--- 缺口候选 (Top {args.top}) " + "-" * 30)
        print("这些名字目标 JS 访问了，但当前环境里不存在：\n")
        for name, cnt in misses.most_common(args.top):
            print(f"  {cnt:5d}x  {name}")
        print()
    else:
        print("未发现缺口 —— 当前环境已覆盖目标 JS 的全部全局探测。\n")

    if gets:
        print(f"--- 访问最频繁 (Top {args.top}) " + "-" * 30)
        for name, cnt in gets.most_common(args.top):
            mark = "  [缺]" if name in misses else ""
            print(f"  {cnt:5d}x  {name}{mark}")
        print()

    if errors:
        print(f"--- 执行中断点 ({len(errors)}) " + "-" * 30)
        for e in errors[:10]:
            print(f"  {e}")
        print()

    if args.emit_profile:
        site_name = args.site or "newsite"
        print("--- 可粘贴进 env/sites/ 的档案骨架 " + "-" * 20)
        print(f"# 由 probe_env.py 自动生成，缺口需人工确认真实浏览器行为后再补")
        print(f"name: {site_name}")
        print("environment:")
        print("  navigator: {}")
        if misses:
            print("polyfills:")
            print(f"  # 待补缺口: {', '.join(list(misses)[:12])}")
            print("  - TODO")
        print("pitfalls:")
        print("  - TODO")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
