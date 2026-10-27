"""对比真实浏览器请求与我方请求的差异，定位 4030 的触发条件。"""

import json
import os

CAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ctrip", "capture.json")

data = json.load(open(CAP, encoding="utf-8"))

# 找目标接口的请求/响应对
target = "getHotelRoomListInland"
reqs = [r for r in data if r["kind"] == "request" and target in r["url"]]
resps = [r for r in data if r["kind"] == "response" and target in r["url"]]

print("=" * 74)
print(f"getHotelRoomListInland: {len(reqs)} 请求 / {len(resps)} 响应")
print("=" * 74)

if reqs:
    r = reqs[0]
    print(f"\nURL: {r['url']}")
    print("\n--- 请求头 ---")
    for k, v in sorted(r["headers"].items()):
        print(f"  {k}: {str(v)[:150]}")
    print("\n--- 请求体 ---")
    try:
        body = json.loads(r["postData"])
        print(json.dumps(body, ensure_ascii=False, indent=2)[:3000])
    except Exception:
        print(str(r["postData"])[:2000])

if resps:
    resp = resps[0]
    print(f"\n--- 响应 {resp['status']} ---")
    try:
        j = json.loads(resp["body"])
        # 只看关键字段，避免刷屏
        d = j.get("data", {})
        print("data keys:", list(d.keys())[:20] if isinstance(d, dict) else type(d))
        if isinstance(d, dict) and "htlSpiderActionErrorCode" in d:
            print("!! htlSpiderActionErrorCode =", d["htlSpiderActionErrorCode"])
        print("body head:", resp["body"][:600])
    except Exception as e:
        print("parse fail:", e, resp["body"][:600])

print("\n" + "=" * 74)
print("全部响应里的风控错误码")
print("=" * 74)
for r in data:
    if r["kind"] == "response":
        if "htlSpiderActionErrorCode" in r.get("body", ""):
            print(f"  {r['status']}  {r['url'][:80]}")
            print(f"      {r['body'][:300]}")

print("\n" + "=" * 74)
print("Akamai / 风控 cookie")
print("=" * 74)
for r in data:
    if r["kind"] == "cookies":
        for c in r["value"]:
            n = c.get("name", "")
            if any(k in n.lower() for k in ("abck", "bm_", "ak_", "fx", "sensor", "cticket", "guid")):
                print(f"  {n}  domain={c.get('domain')}  len={len(str(c.get('value','')))}")
