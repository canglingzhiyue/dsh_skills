"""侦察脚本：探测携程详情页房型接口的保护状况。

目标接口：https://m.ctrip.com/restapi/soa2/33278/getHotelRoomListInland
目的：确认它要什么参数、是否被风控拦、拦的话拦在哪一层。
"""

import os
import httpx

# 本机 NO_PROXY 里含方括号 IPv6 字面量 [::1]，httpx 解析会抛
# InvalidURL: Invalid port: ':1]'。这里只剔除该条目，保留其余排除项。
_np = os.environ.get("NO_PROXY", "")
os.environ["NO_PROXY"] = ",".join(
    p for p in _np.split(",") if p.strip() and not p.strip().startswith("[")
)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

URL = "https://m.ctrip.com/restapi/soa2/33278/getHotelRoomListInland"

HEADERS = {
    "User-Agent": UA,
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://hotels.ctrip.com",
    "Referer": "https://hotels.ctrip.com/",
    "CookieOrigin": "https://hotels.ctrip.com",
    "currency": "CNY",
    "locale": "zh-CN",
    "appid": "100013776",
    "clientid": "09031153110405245224",
    "region": "CN",
}

# 先发一个最小 body，看服务端报什么错 —— 错误信息会告诉我们缺哪些字段
MINIMAL = {
    "hotelId": 95749195,
    "checkIn": "2026-10-10",
    "checkOut": "2026-10-11",
}

# 携程 SOA2 标准 head 结构（按服务端校验要求逐项补齐）
HEAD = {
    "cid": "09031153110405245224",
    "ctok": "",
    "cver": "1.0",
    "lang": "01",
    "sid": "8888",
    "syscode": "09",
    "auth": "",
    "extension": [],
    "platform": "PC",
    "group": "ctrip",
    "bu": "ibu",
}

WITH_HEAD = {
    "head": HEAD,
    "hotelId": 95749195,
    "checkIn": "2026-10-10",
    "checkOut": "2026-10-11",
    "roomFilter": [],
    "pageCode": "10320668146",
    "searchToken": "",
}

# 详情页真实请求通常还带这些
WITH_EXTRA = dict(WITH_HEAD)
WITH_EXTRA.update({
    "adultCount": 2,
    "childCount": 0,
    "childAges": [],
    "isOnlyAcceptRoom": False,
    "useHealthGuard": False,
    "isNeedStaticData": True,
    "isGetSmartPrice": False,
    "isShowVendorPrice": True,
    "abTestInfo": [],
})


def probe(name, body):
    print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
    try:
        with httpx.Client(timeout=30, follow_redirects=True, http2=False) as c:
            r = c.post(URL, headers=HEADERS, json=body)
        print(f"status: {r.status_code}")
        print(f"content-type: {r.headers.get('content-type')}")
        for hk, hv in r.headers.items():
            if hk.lower() in ("c-via", "x-cdn-pop", "server", "server-timing"):
                print(f"  {hk}: {hv[:200]}")
        text = r.text
        print(f"body length: {len(text)}")
        print("--- body head ---")
        print(text[:1500])
    except Exception as e:
        print(f"REQUEST FAILED: {type(e).__name__}: {e}")


if __name__ == "__main__":
    probe("1) 补 platform/group", WITH_HEAD)
    probe("2) 补详情页常见字段", WITH_EXTRA)
