"""用 Camoufox 采集携程接口的真实请求基准。

目的：拿到"真实浏览器发出去的请求长什么样"，作为 iv8 补环境的对照基准。
      这是标准工作流的第一步 —— 不先拿到 ground truth，补环境就是盲补。

产出：demos/_ctrip/capture.json，含每个目标请求的
      URL / method / headers / postData / cookies / 响应摘要。
"""

import json
import os
import sys

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ctrip")
os.makedirs(OUT_DIR, exist_ok=True)

# 要盯的目标接口关键字
WATCH = [
    "getHotelRoomListInland",
    "getHotelListInland",
    "hotel/search",
    "HotelSearch",
    "restapi/soa2",
]

PAGE = "https://hotels.ctrip.com/hotels/95749195.html"
CAPTURE = os.path.join(OUT_DIR, "capture.json")

records = []


def main():
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True, humanize=True) as browser:
        page = browser.new_page()

        def on_request(req):
            url = req.url
            if any(w.lower() in url.lower() for w in WATCH):
                try:
                    post = req.post_data
                except Exception:
                    post = None
                records.append({
                    "kind": "request",
                    "url": url,
                    "method": req.method,
                    "headers": dict(req.headers),
                    "postData": post,
                    "resourceType": req.resource_type,
                })
                print(f"[REQ] {req.method} {url[:120]}")

        def on_response(resp):
            url = resp.url
            if any(w.lower() in url.lower() for w in WATCH):
                try:
                    body = resp.text()[:3000]
                except Exception as e:
                    body = f"<unreadable: {e}>"
                records.append({
                    "kind": "response",
                    "url": url,
                    "status": resp.status,
                    "headers": dict(resp.headers),
                    "body": body,
                })
                print(f"[RESP] {resp.status} {url[:120]}")

        page.on("request", on_request)
        page.on("response", on_response)

        print(f"[nav] {PAGE}")
        page.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        # 尝试滚动，触发懒加载的房型接口
        for _ in range(4):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(1500)

        page.wait_for_timeout(5000)

        # 落 cookie
        try:
            cookies = page.context.cookies()
        except Exception:
            cookies = []
        records.append({"kind": "cookies", "value": cookies})

        print(f"\n[cookies] {len(cookies)} 个")
        for c in cookies:
            nm = c.get("name", "")
            if any(k in nm.lower() for k in ("abck", "bm_sz", "ak_", "sensor", "fx", "_s")):
                print(f"  ★ {nm} = {str(c.get('value'))[:80]}")

        title = page.title()
        print(f"[title] {title}")

    with open(CAPTURE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\n[saved] {CAPTURE}  ({len(records)} 条记录)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
