# 常见坑与解决方案

> 按出现频率排序，附真实案例。

---

## 1. 指纹不一致（最常见）

### 现象
- 服务端返回风控错误码（如 4030、-100、验证失败）
- 响应 200 但业务逻辑拒绝

### 根因
手工覆盖 `environment` 时，改了一处，暴露三处新的不一致。

### 解决
**能不改就不改**。iv8 内置默认指纹在原生一致性上是对的：
- `Object.getOwnPropertyDescriptor(Navigator.prototype,'userAgent').get.toString()` → `function get userAgent() { [native code] }`
- `Symbol.toStringTag` → `[object Navigator]`
- plugins=5, mimeTypes=2（真实 Chrome 也是这个数量级）

**必须改时**：
1. 先用 `get_defaults()` 看默认值
2. 只改必须改的字段
3. 用探针验证改动后是否引入新缺口

### 案例
```python
# 错误：全量覆盖
environment = {
    "navigator": {"userAgent": "...", "platform": "...", ...},  # 几十个字段
    "screen": {...},
    "window": {...},
}

# 正确：只改版本号（如果必须）
environment = {
    "navigator": {"userAgent": "Mozilla/5.0 ... Chrome/124.0.0.0 ..."}
}
```

---

## 2. debugger 被禁用

### 现象
`debugger;` 语句不触发断点。

### 根因
iv8 主动禁用了原生 `debugger`，因为目标 JS 常用无限 `debugger` 循环反调试。

### 解决
用 `vdebugger;` 代替，行为完全一致。

```javascript
// 无效
debugger;

// 有效
vdebugger;
```

---

## 3. console 被检测

### 现象
目标 JS 检测到调试环境，行为异常。

### 根因
某些反爬 JS 通过 `console.log` 的副作用（如性能计时差异）检测调试。

### 解决
1. 关闭标准 console：`with_devtools(..., enable_console=False)`
2. 用 `vconsole` 代替：`vconsole.log()` 只在 DevTools 显示，对目标 JS 不可见

```python
ctx = iv8.JSContext(mode="debug").with_devtools(
    port=9229,
    enable_console=False
)
```

```javascript
// 目标 JS 检测不到
vconsole.log("debug info");
```

---

## 4. 时间模式选错

### 现象
- POW（工作量证明）类算法结果不对
- 时序敏感校验失败

### 根因
`time_mode="logical"`（默认）下，`Date.now()` 不反映真实时间流逝。

### 解决
时间敏感场景用 `time_mode="system"`：

```python
# 错误：逻辑时间
with iv8.JSContext(time_mode="logical") as ctx:
    ctx.eval("var start = Date.now(); /* POW 计算 */")
    # Date.now() 几乎不变

# 正确：系统时间
with iv8.JSContext(time_mode="system") as ctx:
    ctx.eval("var start = Date.now(); /* POW 计算 */")
    # Date.now() 真实流逝
```

---

## 5. 网络请求无响应

### 现象
XHR/fetch 发出去了，但回调永远不触发。

### 根因
iv8 社区版**没有真实网络栈**，请求进离线资源 bundle 匹配。

### 解决
Python 侧发真实请求，注入响应：

```python
import httpx

# 1. iv8 里 JS 发起请求（会被记录到 netLog）
ctx.eval("""
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://api.example.com/data');
    xhr.onload = function() { window._result = xhr.responseText; };
    xhr.send();
""")

# 2. Python 侧发真实请求
resp = httpx.get("https://api.example.com/data")

# 3. 注入响应
ctx.add_resource(
    url="https://api.example.com/data",
    body=resp.text,
    status=resp.status_code
)

# 4. 推进事件循环，触发回调
ctx.eval("window.__iv8__.eventLoop.drain()")
print(ctx.eval("window._result"))
```

---

## 6. 子线程 Illegal invocation

### 现象
子线程里创建 `JSContext`，调用 `appendChild` 等 DOM 方法抛 `Illegal invocation`。

### 根因
iv8 0.1.3 及更早版本的 receiver 校验问题。

### 解决
升级到 0.1.4+：

```bash
uv pip install --python .venv/Scripts/python.exe --upgrade iv8
```

---

## 7. MessageChannel 重复 polyfill

### 现象
加载 polyfill 后功能异常。

### 根因
iv8 0.1.4 已内置 MessageChannel，又加载了 fallback polyfill，覆盖了正确实现。

### 解决
**先用探针确认是否真的缺失**：

```python
# 检查是否已存在
result = ctx.eval("typeof MessageChannel")
if result == "undefined":
    # 才加载 polyfill
    ctx.eval(open("polyfills/messagechannel_fallback.js").read())
```

---

## 8. sleep(5000) 不生效

### 现象
逻辑时间模式下，`setTimeout(fn, 5000)` 立即执行。

### 根因
逻辑时间就是"瞬间完成"，这是特性不是 bug。

### 解决
- 需要真实等待：用 `time_mode="system"`
- 需要快速完成：保持 `logical`，这是优势

---

## 9. IP 地域触发风控

### 现象
完整回放真实请求，仍被风控拦截。

### 根因
出口 IP 与真实浏览器不一致（如代理在日本，目标站风控海外 IP）。

### 解决
1. 确认出口 IP：`httpx.get("https://ipinfo.io/json")`
2. 与浏览器出口一致（通常直连）
3. 或站点档案里记录 `preferred_region: CN`

```python
# 检查当前出口
import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
resp = httpx.get("https://ipinfo.io/json", trust_env=False)
print(resp.json()["country"])  # 应为 CN
```

---

## 10. 一次性 token 失效

### 现象
回放真实请求，token 已失效。

### 根因
`phantom-token` 等是一次性消耗品，用一次就失效。

### 解决
1. 在浏览器里**实时**触发请求，立即使用 token
2. 或找到 token 生成算法，在 iv8 里复现
3. 或接受"每次都要新 token"的成本

---

## 11. 页面加载后接口不触发

### 现象
`page.load` 完成，但目标接口没发请求。

### 根因
接口是用户交互（点击/滚动）或定时器触发的。

### 解决
```python
# 1. 加载页面
ctx.eval("window.__iv8__.page.load({...})")

# 2. 触发交互
ctx.eval("document.getElementById('btn').click()")

# 3. 或推进时间触发定时器
ctx.eval("window.__iv8__.eventLoop.advance(10000)")
```

---

## 12. 探针误报 Symbol.unscopables

### 现象
探针报告 `Symbol(Symbol.unscopables)` 为缺口。

### 根因
`with (proxy)` 方案的固有噪音。

### 解决
已改用 `defineProperty` 方案，不再有此问题。如用旧版探针，忽略该条目。

---

## 13. 携程 4030（htlSpiderActionErrorCode）

### 现象
`getHotelRoomListInland` 返回 `{"data":{"htlSpiderActionErrorCode":4030}}`。

### 根因（已确认）
- 不是 headers/cookies 问题（完整回放也 4030）
- 不是 IP 问题（直连也 4030）
- **高度怀疑**：`phantom-token` 一次性失效，或需要特定时序/行为数据

### 解决（进行中）
1. 在浏览器里实时触发，立即使用 token
2. 或找到 token 生成逻辑，在 iv8 里复现
3. 或接受"需要真实浏览器"的限制

---

## 排查 checklist

遇到问题时按顺序检查：

- [ ] iv8 版本是否最新（`pip show iv8`）
- [ ] time_mode 是否正确（logical vs system）
- [ ] 是否有多余的指纹覆盖（用默认试试）
- [ ] 网络请求是否注入了资源
- [ ] 出口 IP 是否与浏览器一致
- [ ] 目标 JS 是否检测到 `__iv8__`（不应该）
- [ ] 是否有一次性 token/时序要求
