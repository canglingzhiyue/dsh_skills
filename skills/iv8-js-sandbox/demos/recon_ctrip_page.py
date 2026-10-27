"""抓取携程详情页与相关 JS，定位 getHotelRoomListInland 的调用方式。"""

import os
import re
import httpx

_np = os.environ.get("NO_PROXY", "")
os.environ["NO_PROXY"] = ",".join(
    p for p in _np.split(",") if p.strip() and not p.strip().startswith("[")
)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

PAGE = "https://hotels.ctrip.com/hotels/95749195.html"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ctrip")

os.makedirs(OUT, exist_ok=True)


def fetch(url, name):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        print(f"[cache] {name}")
        return open(path, encoding="utf-8", errors="replace").read()
    with httpx.Client(timeout=40, follow_redirects=True) as c:
        r = c.get(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
    print(f"[fetch] {name} -> {r.status_code} {len(r.text)} chars")
    open(path, "w", encoding="utf-8").write(r.text)
    return r.text


html = fetch(PAGE, "detail.html")

print("\n--- 页面里出现的关键词 ---")
for kw in ["getHotelRoomListInland", "htlSpiderActionErrorCode", "4030",
           "_fx", "akamai", "sensor_data", "_abck", "bm_sz", "spider"]:
    n = html.lower().count(kw.lower())
    print(f"  {kw:28s} {n}")

print("\n--- 引用的 JS 文件 ---")
scripts = set(re.findall(r'src="([^"]+\.js[^"]*)"', html))
for s in sorted(scripts):
    print("  ", s[:160])
print(f"  共 {len(scripts)} 个")

# 找 __NEXT_DATA__ 之类的内联状态
for marker in ["__NEXT_DATA__", "window.__INITIAL_STATE__", "searchToken", "htlSpider"]:
    idx = html.find(marker)
    if idx >= 0:
        print(f"\n--- {marker} @ {idx} ---")
        print(html[max(0, idx - 200): idx + 600].replace("\n", " ")[:800])
