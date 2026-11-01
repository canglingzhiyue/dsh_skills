# 抓包工作流（Reqable）

> 标注规则：【实测】= 2026-11-01 在本机跑过；【文档】= 官方文档描述、本机未验证；【推断】= 由实测与文档推出。

## 1. 桌面端抓本机流量【实测】

```
capture_live_set_enabled(enabled=true)      # 起抓包引擎
proxy_set(overrideSystem=true)              # 接管系统代理（本机 autoProxy=false，必须手动开）
让目标自己跑：浏览器 / curl / 你的 Python 脚本 / GUI 程序
capture_live_filter(filters=[{"type":"host","hosts":["api.example.com"]}])
capture_live_get_by_id(id)
```

收尾两步，别忘：

```
proxy_set(overrideSystem=false)             # 还回系统代理
capture_live_set_enabled(enabled=false)
```

- 只抓某个程序：`filters` 的 `application` 形状（`name` / `id` / `pid`）—— 记录里的 `application.name` 就是发起进程名【实测：能识别出 `pwsh`】。
- 想让请求**自己带代理**而不动系统设置：`curl -x http://127.0.0.1:9000 http://target`，效果等价且更干净【实测】。
- 系统代理被别的工具（Clash / v2ray / Fiddler）占着时会互相覆盖，抓包期间只留一个【文档 + 实测现象】。

## 2. HTTPS 解密

Reqable 是 MITM：**客户端必须信任 Reqable 根证书**，否则只能看到 TLS 握手失败或乱码。

| 平台 | 做法 | 状态 |
|---|---|---|
| Windows 本机 | 首次启动跟引导安装；或在 GUI 里点「安装证书」。校验：`Get-ChildItem Cert:\CurrentUser\Root \| ? Subject -match Reqable` | 【实测】本机已装 `CN="Reqable CA (Aug 3, 2025, DEA51A81)"`，`https://www.baidu.com` 正常出明文 |
| Android 7+ | 用户 CA 默认不被 App 信任：需 root + Magisk 把证书塞进 `/system/etc/security/cacerts/`；否则只有 H5/浏览器流量能解 | 【文档 + 通用结论】本机未验证 |
| iOS | 安装描述文件后还要在「关于本机 → 证书信任设置」里手动信任 | 【文档】 |

**只想解某些域名 / 想绕过某些域名**：改 `capture_ssl_proxying` 配置族（`get_config` / `create` / `select`）。本机内置两条：include-all、exclude-all。逆向里常见诉求是「只解目标域，其余直通」，避免无关流量污染与证书告警。

## 3. 本地流量（localhost / 127.0.0.1）【实测有坑】

- 多数客户端访问 `127.0.0.1` 时不走系统代理 → 请求根本进不来。
- 本机 `proxyLoopback: true`，经代理访问 `127.0.0.1:9016` **能拿到 200**，但**不进抓包记录**（`capture_live/filter` 查不到，实测 2 次）。
- 可用替代：① 让客户端显式连 `127.0.0.1:9000`；② 换 `anything-analyzer`（它的内嵌浏览器/会话侧对本地流量更友好）；③ 反向代理功能（`capture_reverse_proxy` 族）把目标挂到一个非 loopback 端口。

## 4. 手机端【文档，本机未验证】

两种模式，选一个：

- **协同模式（推荐）**：手机 Reqable 扫码连桌面端，流量转发到桌面分析。不用同网段改 Wi-Fi 代理，断点/重写/脚本仍由桌面端执行。
- **独立模式**：手机端自己起本地 VPN 抓包，但断点 / 重写 / 脚本**不可用**（系统策略）。
- **传统路线**：手机 Wi-Fi 手填代理 `<电脑IP>:9000` + 装证书。`preferredIp` 本机记录为 `192.168.21.115`（配置项，可能已过期，以实际网卡为准）。

远程遥控手机端 Reqable：`mcp-server.exe --host <手机IP> --port <手机API端口>`（文档：AI 控制非本机 Reqable 的唯一方式）。

## 5. 二级代理（目标在受限网络）

客户端 → Reqable(9000) → 二级代理 → 目标。桌面端 GUI：`代理 → 二级代理 → 添加规则`；也可用 `capture_secondary_proxy_create` 族。
两种模式：允许模式（只放指定域名进二级代理）/ 绕行模式（指定域名绕过）。域名支持 `*` `?`，只填 `*` = 全部。
⚠ 配了但二级代理没开 → 命中它的请求直接失败（表现为「网络不通」）。本机现在是「开关开着、规则为空」，等于没生效。

## 6. 改行为：断点 / 重写 / 脚本 / 限速

| 需求 | 用哪个 | 最短做法 |
|---|---|---|
| 停下来人工看/改一条请求 | 断点 `capture_breakpoint_create` | `url` + `wildcard:true` + `isRequestEnabled`/`isResponseEnabled` |
| 把响应改成 500 / 改成空数组 / 改某个字段 | 重写 `capture_rewrite_create` `action.type=2` | `code=500`、`statusLineEnabled=true`；或 `body:{type:1,payload:"[]"}` |
| 把请求里的 userId 换掉（越权测试） | 重写 `action.type=3`（Modify Request） | `modifies[{type:2,modify:{pattern:"oldId",replacement:"newId"}}]` |
| 响应做 AES 解密 / 打印明文 | 脚本 `capture_script_create` | **先** `script_framework` + `script_template` 拿框架，再写 `code` |
| 弱网 / 3G 延迟 | `capture_network_throttling_create` + `select` | `{name, host:"*", mode}` |
| 复制一份流量给另一个服务 | 镜像 `capture_mirror_create` | 见 mcp-tools.md 的统一骨架 |
| 把某条请求重放到别的后端 | 反向代理 `capture_reverse_proxy_create` | — |

建完**必须** `*_set_enabled(true)`（总开关）并确认 `*_list` 里 `isEnabled=true`。收尾关掉规则，否则下次抓包还带着上次的注入。

## 7. 分析 / 资产化 / 回归

- **转 cURL**：`capture_live_generate_curl(id)` → 直接进重放、CI 冒烟、pytest 骨架。
- **转 API 标签页**：`capture_live_compose(id)`。
- **入集合**：`capture_live_collection_add(id, collectionId)` / `collection_api_create(collectionId, curl)`（**集合要登录 + 高级版**）。
- **接口 diff / 变更感知**：GUI 里选中两条记录用「对比」；Agent 侧则把两条记录的响应体取出后自己比。两轮抓包（迭代前后）各存一份，比字段增删与类型变化。
- **HAR 留档**：GUI 支持导入导出 HAR【文档】，适合把一轮流量落成文件进案件库 `data\`。

## 8. 逆向里的典型组合

| 任务 | 组合 |
|---|---|
| 某 App/网页的接口清单 | 本技能抓包 → `capture_live_filter` 按 host/app 筛 → 批量 `capture_live_get_by_id` → 生成 cURL/集合 → 落到案件 `data\` |
| 定位签名参数来源 | 抓包（本技能或 anything-analyzer）拿完整请求 → Web 域转 `camoufox-reverse` 下 Hook 找生成点 → 回到本技能用**重写规则**改参数验证服务端是否校验 |
| 服务端校验强度测试 | 重写 `type=3`（改 userId/orderId）+ 观察响应 → 判断水平越权 |
| 前端容错回归 | 重写 `type=2` 注异常（500 / 空数组 / 截断 / 删字段）+ 手点页面看兜底 |
| 补丁后回归 | `firerpa` 驱动 App 走流程 + 本技能（或 anything-analyzer）读流量比对 |

## 9. 验收（照 SKILL.md §3）

抓到的要能读全、能重放、规则要能被直接观察到生效、收尾不留残留。「工具返回 200」不是证据。
