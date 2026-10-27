"""回放真实浏览器请求，再用消融法定位 4030 的真正触发条件。

方法：
  1. 完整回放（headers + cookies + body）-> 预期成功
  2. 逐项移除可疑头部 -> 看哪一项移除后复现 4030
  3. 结论：4030 的最小必需集
"""

import json
import os
import httpx

_np = os.environ.get("NO_PROXY", "")
os.environ["NO_PROXY"] = ",".join(
    p for p in _np.split(",") if p.strip() and not p.strip().startswith("[")
)

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "_ctrip", "capture.json")

data = json.load(open(CAP, encoding="utf-8"))
target = "getHotelRoomListInland"
req = next(r for r in data if r["kind"] == "request" and target in r["url"])
cookies = next(r["value"] for r in data if r["kind"] == "cookies")

URL = req["url"]
BODY = req["postData"]
H = dict(req["headers"])

# httpx 不接受这些由它自己管的头
for k in ("host", "content-length", "connection", "accept-encoding"):
    H.pop(k, None)

JAR = {c["name"]: c["value"] for c in cookies}


def call(headers, jar, label, body=None, direct=True):
    # 关键：必须直连。走本机 7890 代理时出口在日本（x-cdn-pop: JP），
    # 携程风控对海外 IP 直接返回 htlSpiderActionErrorCode=4030。
    try:
        client = httpx.Client(timeout=30, follow_redirects=False, trust_env=not direct)
        with client as c:
            r = c.post(URL, headers=headers, cookies=jar,
                       content=(body if body is not None else BODY).encode())
        txt = r.text
        blocked = "htlSpiderActionErrorCode" in txt
        code = ""
        if blocked:
            try:
                code = json.loads(txt)["data"].get("htlSpiderActionErrorCode")
            except Exception:
                code = "?"
        verdict = f"被拦(码={code})" if blocked else ("成功" if r.status_code == 200 else f"HTTP {r.status_code}")
        print(f"  {label:42s} -> {verdict}   [{len(txt)}B]")
        return not blocked and r.status_code == 200
    except Exception as e:
        print(f"  {label:42s} -> 异常 {type(e).__name__}: {e}")
        return False


print("=" * 78)
print("阶段一：基线完整性验证")
print("=" * 78)
full_ok = call(H, JAR, "完整回放（全部头+cookie）")
print(f"\n  完整头数量: {len(H)}   cookie 数量: {len(JAR)}")

print("\n" + "=" * 78)
print("阶段二：消融测试 —— 逐个移除可疑项")
print("=" * 78)

SUSPECTS = ["phantom-token", "x-ctx-wclient-req", "cookieorigin",
            "x-ctx-ubt-pageid", "x-ctx-ubt-vid", "x-ctx-ubt-sid", "x-ctx-ubt-pvid",
            "x-ctx-country", "x-ctx-currency", "x-ctx-locale", "origin", "referer"]
for s in SUSPECTS:
    if s not in H:
        continue
    h2 = {k: v for k, v in H.items() if k != s}
    call(h2, JAR, f"去掉 {s}")

print("\n" + "=" * 78)
print("阶段三：只保留最小集")
print("=" * 78)
MIN = {k: v for k, v in H.items()
       if k in ("user-agent", "content-type", "accept", "origin", "referer",
                "phantom-token", "cookieorigin")}
call(MIN, JAR, "最小集（7 头 + 全 cookie）")
call(MIN, {}, "最小集但无 cookie")
call(MIN, {"ak_bmsc": JAR.get("ak_bmsc", "")}, "最小集 + 仅 ak_bmsc")
call(MIN, {"bm_sv": JAR.get("bm_sv", "")}, "最小集 + 仅 bm_sv")

print("\n" + "=" * 78)
print("阶段四：phantom-token 的角色")
print("=" * 78)
if "phantom-token" in H:
    tok = H["phantom-token"]
    print(f"  token 长度: {len(tok)}")
    print(f"  token 前缀: {tok[:40]}")
    h_no_tok = {k: v for k, v in H.items() if k != "phantom-token"}
    call(h_no_tok, JAR, "去掉 phantom-token（其余全保留）")
    fake = dict(H)
    fake["phantom-token"] = "1005-common-" + "A" * (len(tok) - 12)
    call(fake, JAR, "phantom-token 换成伪造值")
