# iv8 API 速查表

> 基于 iv8 0.1.4，官方文档见 https://github.com/HanZzzzz000/iv8

---

## 快速开始

```python
import iv8

with iv8.JSContext() as ctx:
    result = ctx.eval("1 + 2")  # 3
```

---

## JSContext 构造参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `mode` | str | `"prod"` | `"prod"` 零开销 / `"debug"` 启用监控 |
| `environment` | dict | None | 浏览器指纹配置 |
| `config` | dict | None | 框架行为配置 |
| `time_mode` | str | `"logical"` | `"logical"` 逻辑时间 / `"system"` 真实时间 |
| `js_api` | str | `"__iv8__"` | JS 侧工具对象挂载名 |
| `ignore_apis` | list | 内置 | debug 模式排除的 API |

---

## 核心方法

### eval(source, to_py=False)

执行 JS 代码。

```python
ctx.eval("1 + 2")                    # 3
ctx.eval("({a: 1})", to_py=True)     # {'a': 1}（递归转 Python 类型）
ctx.eval("[1,2,3]", to_py=True)      # [1, 2, 3]
```

### add_resource(url, body, status=200, headers=None)

注入离线 HTTP 响应（XHR/fetch 从这里匹配）。

```python
ctx.add_resource(
    url="https://api.example.com/data",
    body='{"result": "ok"}',
    status=200,
    headers={"content-type": "application/json"}
)
```

### expose(obj, name=None)

暴露 Python 对象到 JS 的 `__iv8__.data`。

```python
def my_func(x):
    return x * 2

ctx.expose(my_func)           # JS: __iv8__.data.my_func(21)
ctx.expose(my_func, "double") # JS: __iv8__.data.double(21)
ctx.expose(get=requests.get)  # JS: __iv8__.data.get(url)
```

### with_devtools(port=9229, watch_apis=None, enable_console=True)

启用 DevTools 调试。

```python
ctx = iv8.JSContext(mode="debug").with_devtools(
    port=9229,
    watch_apis=["navigator.userAgent", "document.cookie"],
    enable_console=False  # 关闭标准 console，用 vconsole
)
```

### get_defaults()

获取所有支持的 environment/config 路径及默认值。

```python
defaults = iv8.JSContext.get_defaults()
for path, value in sorted(defaults.items()):
    print(f"{path} = {value!r}")
```

---

## JS 侧工具对象（`window.__iv8__`）

**注意**：`typeof window.__iv8__ === "undefined"`，对目标 JS 不可见。

### 事件循环控制

| 方法 | 说明 |
|------|------|
| `eventLoop.advance(total, step?)` | 分帧推进虚拟时间 |
| `eventLoop.sleep(ms, max?)` | 推进虚拟时间 |
| `eventLoop.tick(ms?)` | 推进并执行一轮 |
| `eventLoop.drain(max?)` | 排空到期任务 |
| `eventLoop.drainMicrotasks()` | 只排空微任务 |
| `eventLoop.drainTimers()` | 只处理定时器 |

```javascript
// 逻辑时间模式下，sleep(5000) 瞬间完成
window.__iv8__.eventLoop.sleep(5000);
```

### 页面加载

```javascript
window.__iv8__.page.load({
    baseURL: 'https://example.com',
    html: '<html>...</html>',
    resources: {
        'https://example.com/app.js': 'var APP = true;'
    },
    headers: [['content-type', 'text/html']]
});
```

### 输入事件

```javascript
// 派发 isTrusted=true 的鼠标事件
window.__iv8__.input.dispatchMouseEvent({
    type: 'click',
    target: document.getElementById('btn'),
    clientX: 50, clientY: 25,
    button: 0
});
```

### 函数伪装

```javascript
// 把 JS 函数伪装成原生函数
var myFunc = window.__iv8__.wrapNative(function(x) { return x * 2; }, 'myFunc');
myFunc.toString();  // "function myFunc() { [native code] }"
```

### 网络日志

```javascript
window.__iv8__.netLog.entries;
// [{url, method, headers, timestamp, ...}, ...]
```

### 帮助

```javascript
window.__iv8__.help();  // 打印所有可用工具
```

---

## 环境配置（environment）

### 结构

```python
environment = {
    "navigator": {
        "userAgent": "...",
        "platform": "Win32",
        "language": "zh-CN",
        "languages": ["zh-CN", "en-US"],
        "hardwareConcurrency": 8,
        "deviceMemory": 8,
        "webdriver": False,
    },
    "screen": {
        "width": 1920,
        "height": 1080,
        "colorDepth": 24,
    },
    "window": {
        "innerWidth": 1920,
        "innerHeight": 947,
        "devicePixelRatio": 1.0,
    },
    "location": {
        "href": "https://example.com/page",
    },
    "webgl": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, ...)",
    },
}
```

### 查看所有可配置项

```python
defaults = iv8.JSContext.get_defaults()
print(f"共 {len(defaults)} 项")

# 按前缀筛选
for path, value in sorted(defaults.items()):
    if path.startswith("navigator."):
        print(f"{path} = {value!r}")
```

---

## 时间模式

| 模式 | 说明 | 适用 |
|------|------|------|
| `logical` | 纯逻辑推进，`sleep(5000)` 瞬间完成 | 自动化、快速执行 |
| `system` | 系统时间锚定，`Date.now()` 反映真实耗时 | 时间敏感场景（POW、时序校验） |

```python
# 逻辑时间（默认）
with iv8.JSContext(time_mode="logical") as ctx:
    ctx.eval("setTimeout(() => log.push('done'), 5000)")
    ctx.eval("window.__iv8__.eventLoop.drain()")  # 瞬间完成

# 系统时间
with iv8.JSContext(time_mode="system") as ctx:
    ctx.eval("var start = Date.now(); while(Date.now()-start < 1000);")
    # 真的会等 1 秒
```

---

## 多线程

每个 `JSContext` 独占一个 V8 Isolate，执行期释放 GIL。

```python
import threading

def run_js(thread_id):
    with iv8.JSContext(environment={"navigator": {"userAgent": f"Bot/{thread_id}"}}) as ctx:
        return ctx.eval("navigator.userAgent")

threads = [threading.Thread(target=run_js, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**性能**：8 线程实测 ~4.7x 加速。

---

## 调试

### 断点

```javascript
// 标准 debugger 被禁用（防反调试）
vdebugger;  // 用这个代替
```

### 隐蔽 console

```javascript
// enable_console=False 时，标准 console 不上报
vconsole.log("调试信息");  // 只在 DevTools Console 显示
```

### API 监控

debug 模式自动记录：
- 浏览器 API 的属性读/写
- 方法调用与构造调用
- JS 内置反射路径（Object.keys、Reflect.ownKeys 等）

---

## 性能参考

| 指标 | 数据 |
|------|------|
| JSContext 创建+销毁 | ~3.3 ms/次 |
| 简单 eval 吞吐 | ~950,000 ops/s |
| 浏览器 API 调用 | 340,000-570,000 ops/s |
| 真实网页 DOM 解析（440KB） | ~7 ms/页 |
| 首次加载内存 | +15 MB |
| 8 线程加速比 | ~4.7x |

---

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `MessageChannel is not defined` | iv8 版本过老 | 升级或加载 polyfill |
| `Illegal invocation` | 子线程首次创建 Context | 0.1.4 已修复，升级 |
| `sleep(5000)` 不生效 | time_mode=system | 改用 logical 或 drain() |
| XHR 无响应 | 未注入资源 | `add_resource()` 或 `page.load.resources` |
| `__iv8__ is not defined` | 自定义了 js_api 名 | 用配置的名字或恢复默认 |
