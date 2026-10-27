# iv8-js-sandbox —— 纯 Python 的 JS 环境模拟与风控参数获取

> 基于 [iv8](https://github.com/HanZzzzz000/iv8) 的轻量逆向技能：不用启动浏览器，
> 在 Python 里直接运行依赖 Web 环境的 JavaScript，批量产出风控签名参数。

---

## 定位与边界

| 维度 | 说明 |
|------|------|
| **适用** | 目标 JS 可在纯 V8 环境运行、只需算法结果（签名/参数/加密串） |
| **不适用** | 需要真实浏览器渲染、真实用户行为轨迹、复杂 WebGL 场景 |
| **合规** | iv8 社区版限**个人学习研究**，禁商用、禁反编译。商用需 Pro 授权 |

**与 camoufox-reverse 的分工**：
- **iv8** —— 轻量、毫秒级、可多线程、无浏览器开销。适合"算出签名"。
- **camoufox** —— 真实浏览器指纹、行为模拟、Cloudflare 对抗。适合"看起来像真人"。
- **选择标准**：先判断目标签名能否脱离浏览器算出来。能 → iv8；不能 → camoufox。

---

## 核心工作流（四步）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. 侦察     │ --> │  2. 补环境   │ --> │  3. 执行     │ --> │  4. 桥接网络 │
│  抓真实请求   │     │  探针+站点档案│     │  iv8 里跑 JS │     │  Python 发请求│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 1. 侦察（抓真实请求）

**必须先拿到 ground truth**，否则补环境是盲补。

```bash
# 用 camoufox 抓真实请求（推荐）
cd D:\AI_python\camoufox
python bin\capture_traffic.py --url https://target.com/page --watch "api/sign"

# 或手动：浏览器 DevTools -> Network -> 右键请求 -> Copy as cURL
```

产出：真实请求的完整 headers + body + cookies。

### 2. 补环境（探针 + 站点档案）

```bash
# 探针：发现目标 JS 探测了什么、我们缺什么
python scripts\probe_env.py -f target.js --site mysite

# 根据探针结果，编辑站点档案
code env\sites\mysite.yml
```

**成长机制**：每次确认有效的差异，沉淀到 `env/`：
- 通用指纹 → `env/base.py`（被 3+ 站点重复覆盖时才提升）
- 缺失 API → `env/polyfills/`（写 .js + manifest.json 索引）
- 站点特有 → `env/sites/<name>.yml`

### 3. 执行（iv8 里跑 JS）

```bash
# 直接执行
python scripts\iv8_run.py -f target.js --site mysite --eval "window.result"

# 或 Python API
python -c "
import sys; sys.path.insert(0, r'env')
import _envlib, iv8

env = _envlib.build_environment(site='mysite')
with iv8.JSContext(environment=env) as ctx:
    ctx.eval(open('target.js').read())
    print(ctx.eval('window.result'))
"
```

### 4. 桥接网络（Python 发真实请求）

**iv8 社区版没有真实网络栈**。所有网络请求必须 Python 侧完成。

```python
import httpx

# iv8 算出签名
sign = ctx.eval("window.sign('params')")

# Python 侧发真实请求
resp = httpx.post("https://api.target.com/data", 
                  headers={"X-Sign": sign},
                  json={"key": "value"})
```

---

## 环境库结构（成长型核心）

```
env/
├── base.py                 # 基线指纹（Chrome/Win 桌面）
│                           # 原则：能不改就不改，iv8 默认已很真
│
├── polyfills/              # 缺失 API 补丁（累积）
│   ├── manifest.json       # 索引：哪个补丁对应什么症状
│   ├── messagechannel_fallback.js
│   └── akamai_surface.js
│
├── patches/                # 反检测补丁（行为层面）
│   └── (如 toString 伪装、时序修正)
│
└── sites/                  # 站点档案（一个站一份）
    ├── akamai.yml          # 示例：Akamai 通用档案
    └── <name>.yml          # 新站点从这里复制
```

### 站点档案模板

```yaml
name: mysite
kind: 目标站点类型（电商/政务/内容平台）
tags: [tag1, tag2]

# 只写该站特有的差异，通用的进 base.py
environment:
  navigator:
    userAgent: "Mozilla/5.0 ..."
    # 版本号必须与该站实际下发的资源匹配

# 需要加载的 polyfill
polyfills:
  - akamai-surface

# 运行时策略
runtime:
  time_mode: system      # logical=快速，system=真实时间（POW/时序敏感用）
  needs_real_network: true

# 已知坑（重要！）
pitfalls:
  - "该站 cookie 有效期 30 分钟，过期需重新获取"
  - "签名算法在 window._sign 上，不在全局"
```

---

## 关键 API 速查

| 场景 | 代码 |
|------|------|
| 创建上下文 | `with iv8.JSContext(environment=env) as ctx:` |
| 执行 JS | `ctx.eval("1+2")` |
| 加载页面 | `ctx.eval("window.__iv8__.page.load({baseURL:..., html:...})")` |
| 注入离线资源 | `ctx.add_resource(url, body, status=200, headers={})` |
| 暴露 Python 函数 | `ctx.expose(my_func, "myFunc")` → JS 里 `__iv8__.data.myFunc()` |
| 推进事件循环 | `ctx.eval("window.__iv8__.eventLoop.drain()")` |
| 查看可配置项 | `iv8.JSContext.get_defaults()` |
| 函数伪装 | `ctx.eval("window.__iv8__.wrapNative(fn, 'name')")` |
| 网络日志 | `ctx.eval("window.__iv8__.netLog.entries", to_py=True)` |

完整 API 见 [references/api-cheatsheet.md](references/api-cheatsheet.md)。

---

## 必踩的坑

| 坑 | 现象 | 解决 |
|---|---|---|
| **debugger 被禁用** | `debugger;` 不触发断点 | 用 `vdebugger;` 代替 |
| **console 被检测** | 反爬 JS 检测 console 行为差异 | 用 `vconsole.log()` 代替 |
| **时间模式选错** | POW 类算法结果不对 | `time_mode="system"`（真实时间） |
| **无网络栈** | XHR/fetch 无响应 | Python 侧发请求，`add_resource` 注入 |
| **指纹不一致** | 服务端返回风控错误 | **不要手动改指纹**，用 iv8 默认 |
| **__iv8__ 可检测** | 目标 JS 检测到 `window.__iv8__` | 正常，`typeof __iv8__ === "undefined"` |

完整坑列表见 [references/pitfalls.md](references/pitfalls.md)。

---

## 调试手法

### DevTools 远程调试

```python
with iv8.JSContext(mode="debug").with_devtools(port=9229) as ctx:
    ctx.eval("vdebugger;")  # Chrome DevTools 里断点
```

### API 访问断点

```python
.with_devtools(
    port=9229,
    watch_apis=["navigator.userAgent", "document.cookie"],
    enable_console=False,  # 关闭标准 console，用 vconsole
)
```

### 网络行为分析

```python
ctx.eval("window.__iv8__.netLog.entries", to_py=True)
# 返回 [{url, method, headers, ...}, ...]
```

---

## 脚本使用

### iv8_run.py —— 统一运行入口

```bash
# 执行 JS 文件
python scripts\iv8_run.py -f target.js --site akamai

# 执行表达式
python scripts\iv8_run.py -e "navigator.userAgent"

# 执行后取值
python scripts\iv8_run.py -f target.js --eval "window.result"

# 查看最终环境
python scripts\iv8_run.py --site akamai --show-env

# debug 模式
python scripts\iv8_run.py -f target.js --debug
```

### probe_env.py —— 环境探针

```bash
# 探针：发现缺口
python scripts\probe_env.py -f target.js --site mysite

# 只看高频访问
python scripts\probe_env.py -f target.js --top 40

# 输出站点档案骨架
python scripts\probe_env.py -f target.js --site newsite --emit-profile
```

### harvest.py —— 沉淀发现

```bash
# 把探针发现沉淀成站点档案补丁
python scripts\harvest.py --site mysite --probe-output probe.json
```

### new_site.py —— 新建站点档案

```bash
# 交互式创建
python scripts\new_site.py

# 或命令行
python scripts\new_site.py --name mysite --url https://example.com
```

---

## 合规与免责

1. **iv8 许可证**：社区版限个人学习研究，禁商用、禁反编译、禁再分发。
2. **目标网站**：遵守 robots.txt 和服务条款，控制请求频率。
3. **数据用途**：仅用于安全研究、自动化测试、学习目的。
4. **责任**：使用者自行承担滥用后果。

---

## 参考

- [iv8 官方文档](https://github.com/HanZzzzz000/iv8)
- [API 速查](references/api-cheatsheet.md)
- [常见坑](references/pitfalls.md)
- [Akamai 专项](references/akamai.md)
