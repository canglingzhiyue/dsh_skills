# Akamai 专项指南

> Akamai Bot Manager 是常见的企业级反爬方案，携程、部分银行、政务站点使用。

---

## 识别特征

| 特征 | 说明 |
|------|------|
| **Cookie** | `_abck`、`bm_sz`、`ak_bmsc`、`bm_sv` |
| **响应头** | `c-via: akamai`、`x-cdn-pop: <地区代码>` |
| **JS 变量** | `window.Akamai`、`window.bmak`、`window.sensor_data` |
| **行为** | 首次访问下发 challenge，通过后放行 |

---

## 两种模式

### 基础模式（较常见）

- 只有 `ak_bmsc`、`bm_sv` cookie
- 无 `_abck` 强校验
- **相对容易突破**

### 强校验模式（高价值目标）

- `_abck` cookie 存在，有 `~` 和 `~-1~` 两种状态
- `~-1~` 表示已被标记异常
- 需要 `sensor_data` 包含真实行为数据
- **iv8 难以独立完成**，需 camoufox 配合

---

## iv8 适用性评估

| 场景 | 可行性 | 说明 |
|------|--------|------|
| 基础模式，纯算法签名 | ✅ 可行 | iv8 足够 |
| 基础模式，需真实时序 | ⚠️ 部分可行 | 用 `time_mode="system"` |
| 强校验，sensor_data | ❌ 不可行 | 需真实鼠标轨迹 |
| 强校验，多次往返 | ❌ 不可行 | cookie 累积需真实会话 |

---

## 实战：携程案例

### 确认 Akamai

```python
# 响应头
c-via: akamai
x-cdn-pop: JP  # 出口节点

# Cookie
ak_bmsc = 96104FF38E1CD7344DE9DDA91B887349~...
bm_sv = 92D423C98100C962D4F2110446FE4C67~...
```

**结论**：基础模式，无 `_abck`。

### 4030 问题

`htlSpiderActionErrorCode: 4030` 是携程**自有风控**，不是 Akamai 直接拦截。

已排除：
- ❌ headers/cookies 不完整（完整回放也 4030）
- ❌ IP 地域（直连也 4030）
- ❌ 参数缺失（已按校验要求补齐）

**高度怀疑**：
- `phantom-token` 一次性失效
- 或需要特定时序/行为数据

### 突破思路

1. **实时 token**：浏览器里触发请求，立即提取 token 使用
2. **算法复现**：找到 `phantom-token` 生成 JS，在 iv8 里跑
3. **降级方案**：接受需要 camoufox 的限制

---

## 通用对抗策略

### 1. Cookie 管理

```python
# 不要伪造 _abck / bm_sz
# 它们是服务端下发并在多次请求间累积的

# 正确做法：真实会话中获取
cookies = {
    "ak_bmsc": "从真实浏览器获取",
    "bm_sv": "从真实浏览器获取",
    # _abck 不存在就不带
}
```

### 2. 时序对齐

```python
# sensor_data 里的时间戳是相对页面加载的毫秒数
# 必须用 system 模式

with iv8.JSContext(time_mode="system") as ctx:
    # Date.now() 真实流逝
    pass
```

### 3. 行为数据

```python
# iv8 无法生成真实鼠标轨迹
# 需要 camoufox 录制后注入

# 或接受限制：只突破无行为校验的接口
```

---

## 调试技巧

### 1. 定位 Akamai 脚本

```javascript
// 在 DevTools 里
window.Akamai  // 存在则确认
window.bmak    // 可能存在
```

### 2. 监控 sensor_data

```javascript
// hook 常见上报点
var orig = navigator.sendBeacon;
navigator.sendBeacon = function(url, data) {
    if (url.includes("akamai") || url.includes("sensor")) {
        console.log("sensor_data:", data);
    }
    return orig.apply(this, arguments);
};
```

### 3. 断点调试

```python
.with_devtools(
    port=9229,
    watch_apis=["navigator.sendBeacon", "XMLHttpRequest.prototype.send"]
)
```

---

## 站点档案模板（Akamai）

```yaml
name: akamai-target
kind: Akamai 防护站点
tags: [akamai]

environment:
  navigator:
    userAgent: "Mozilla/5.0 ... Chrome/124.0.0.0 ..."
    # 必须与站点实际下发资源匹配

polyfills:
  - akamai-surface

runtime:
  time_mode: system      # 必须真实时间
  needs_real_network: true
  warmup_rounds: 2       # 首次加载后等待往返

pitfalls:
  - "_abck 有 ~ 和 ~-1~ 两种状态，后者表示已被标记"
  - "sensor_data 时间戳必须递增，不能复用"
  - "类名混淆度高，用 DevTools 断点定位，不要硬读源码"
```

---

## 参考

- [Akamai Bot Manager 官方文档](https://www.akamai.com/products/bot-manager)
- [携程案例](../demos/recon_ctrip_roomlist.py)
