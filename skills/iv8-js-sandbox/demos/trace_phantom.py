"""在浏览器里追踪 phantom-token 的来源。

手法（也是技能 references 里要沉淀的标准套路）：
  1. hook XMLHttpRequest.prototype.setRequestHeader / open，记录调用栈
  2. hook fetch
  3. 检索 JS 源码里的 phantom-token 引用
  4. 判断它是"服务端下发"还是"客户端生成"
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_ctrip")
os.makedirs(OUT, exist_ok=True)

PAGE = "https://hotels.ctrip.com/hotels/95749195.html"

HOOK = r"""
window.__PHANTOM_LOG__ = { sets: [], callStacks: [], sources: [] };

(function () {
  var LOG = window.__PHANTOM_LOG__;

  function stack() {
    try { throw new Error('trace'); } catch (e) {
      return (e.stack || '').split('\n').slice(1, 12).join('\n');
    }
  }

  // --- hook XHR ---
  var origOpen = XMLHttpRequest.prototype.open;
  var origSet = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.setRequestHeader = function (k, v) {
    if (String(k).toLowerCase() === 'phantom-token') {
      LOG.sets.push({ via: 'xhr.setRequestHeader', key: k, len: String(v).length,
                      head: String(v).slice(0, 40) });
      LOG.callStacks.push(stack());
    }
    return origSet.apply(this, arguments);
  };

  XMLHttpRequest.prototype.open = function (m, u) {
    this.__url__ = u;
    return origOpen.apply(this, arguments);
  };

  // --- hook fetch ---
  var origFetch = window.fetch;
  window.fetch = function (input, init) {
    try {
      var h = (init && init.headers) || {};
      var v = null;
      if (h && typeof h.get === 'function') v = h.get('phantom-token');
      else if (h) v = h['phantom-token'] || h['Phantom-Token'];
      if (v) {
        LOG.sets.push({ via: 'fetch', len: String(v).length, head: String(v).slice(0, 40) });
        LOG.callStacks.push(stack());
      }
    } catch (e) {}
    return origFetch.apply(this, arguments);
  };

  // --- 扫描全局与常见存储位点 ---
  window.__PHANTOM_SCAN__ = function () {
    var found = {};
    ['phantomToken', 'phantom_token', 'phantom-token'].forEach(function (k) {
      try { if (window[k] !== undefined) found['window.' + k] = String(window[k]).slice(0, 60); } catch (e) {}
    });
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var lk = localStorage.key(i);
        if (/phantom/i.test(lk)) found['localStorage.' + lk] = String(localStorage.getItem(lk)).slice(0, 60);
      }
    } catch (e) {}
    try {
      for (var j = 0; j < sessionStorage.length; j++) {
        var sk = sessionStorage.key(j);
        if (/phantom/i.test(sk)) found['sessionStorage.' + sk] = String(sessionStorage.getItem(sk)).slice(0, 60);
      }
    } catch (e) {}
    try {
      if (/phantom/i.test(document.cookie)) {
        found['cookie'] = document.cookie.match(/[^;]*phantom[^;]*/i);
      }
    } catch (e) {}
    return found;
  };
})();
"""


def main():
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True, humanize=True) as browser:
        page = browser.new_page()
        page.add_init_script(HOOK)

        print(f"[nav] {PAGE}")
        page.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)

        log = page.evaluate("window.__PHANTOM_LOG__")
        print(f"\n--- phantom-token 设置次数: {len(log['sets'])} ---")
        for s in log["sets"][:5]:
            print(" ", json.dumps(s, ensure_ascii=False))

        if log["callStacks"]:
            print("\n--- 首个调用栈 ---")
            print(log["callStacks"][0][:1500])

        scan = page.evaluate("window.__PHANTOM_SCAN__()")
        print(f"\n--- 全局/存储中的 phantom 痕迹 ---")
        print(json.dumps(scan, ensure_ascii=False, indent=2))

        # 扫描所有已加载脚本里对 phantom 的引用
        print("\n--- 脚本源码中的 phantom 引用 ---")
        hits = page.evaluate(r"""
        (async () => {
          const out = [];
          const urls = performance.getEntriesByType('resource')
            .filter(e => e.name.endsWith('.js')).map(e => e.name);
          for (const u of urls.slice(0, 40)) {
            try {
              const t = await (await fetch(u)).text();
              const idx = t.indexOf('phantom-token');
              if (idx >= 0) out.push({ url: u, idx: idx, ctx: t.slice(Math.max(0, idx-260), idx+260) });
            } catch (e) {}
          }
          return out;
        })()
        """)
        for h in hits:
            print(f"\n  ★ {h['url'][:110]}")
            print(f"    {h['ctx'][:520]}")

        with open(os.path.join(OUT, "phantom_trace.json"), "w", encoding="utf-8") as f:
            json.dump({"log": log, "scan": scan, "hits": hits}, f,
                      ensure_ascii=False, indent=2)
        print(f"\n[saved] {os.path.join(OUT, 'phantom_trace.json')}")


if __name__ == "__main__":
    main()
