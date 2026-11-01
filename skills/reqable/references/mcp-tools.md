# Reqable MCP 工具地图（reqable-mcp v1.0.1，2026-11-01 实测）

`--scope all` = **146** 个工具，`--scope minimal` = **48** 个。分组（按实测名字统计）：

| 前缀 | 数量 | 说明 |
|---|---|---|
| `capture_*` | **112** | 抓包相关的全部配置能力，见下方 12 个子族 |
| `collection_*` | 16 | 接口集合（需登录 + 高级版，社区版会失败） |
| `environment_*` | 8 | 环境变量组 |
| `rest_*` | 7 | 新建 API 标签页（HTTP / WebSocket / gRPC / raw） |
| `script_*` | 2 | `script_framework` / `script_template`（写脚本前必读） |
| `proxy_*` | 1 | `proxy_set`（系统代理开关） |

## 1. 抓包列表（最常用，8 个）

| 工具 | 用途 / 关键参数 |
|---|---|
| `capture_live_set_enabled` | `enabled: bool` 启停抓包 |
| `capture_live_status` | 返回 `{"status":"active"\|"inactive"}` |
| `capture_live_filter` | **只返回 ID 数组**；`filters` 数组，多项 AND（见 §2） |
| `capture_live_get_by_id` | `id: int`，返回完整记录（含 `application.name` = 发起进程） |
| `capture_live_generate_curl` | `id: int` → 可直接重放的 cURL |
| `capture_live_compose` | `id: int` → 组装成 HTTP/WebSocket API 标签页 |
| `capture_live_clear` | 清空当前实时记录 |
| `capture_live_collection_add` | `id` + `collectionId` 入库 |

## 2. `capture_live_filter` 的 `filters` 形状（★最容易写错）

`filters` 是数组，每项是 `oneOf` 七种之一，**多项之间逻辑 AND**：

```jsonc
// 1) 关键字：跨 URL / 头 / body / 地址模糊搜
{"type":"keyword","pattern":"token","caseSensitive":false,"regex":false}
// 2) 精确 URL 列表
{"type":"url","urls":["https://api.example.com/v1/user"]}
// 3) 精确 host
{"type":"host","hosts":["www.baidu.com"]}
// 4) 远端 IP
{"type":"ip","ips":["1.2.3.4"]}
// 5) HTTP 方法
{"type":"method","methods":["POST"]}
// 6) 响应码（整数）
{"type":"code","codes":[200,302]}
// 7) 客户端应用（最关键的一条：抓「谁发的」）
{"type":"application","name":"pwsh"}        // 也可用 id（包名/bundle id）或 pid
```

实测：`POST /capture/live/filter {"filters":[{"type":"host","hosts":["www.baidu.com"]}]}` → `[2,3]`。
错误形状的报错是 `400 {"message":"filters is required","status":400}`（把 filters 写成对象而非数组、或整个漏掉时）。

## 3. 规则类子族的统一骨架（7 个族共用一套模式）

> ⚠ **未登录账号时这一整节只是「设计说明」，实际不可写**：2026-11-01 实测，`capture_rewrite_create` / `capture_breakpoint_create` / `capture_network_throttling_create` / `capture_ssl_proxying_create` / `collection_create` / `environment_create` 全部返回
> `… requires an account, please login to your Reqable account.`
> **可读可开关、不可创建**：`*_get_config` / `*_list` / `*_lookup` / `*_get_active` / `*_set_enabled` 都正常。详见 SKILL.md 坑 4。

`breakpoint` / `gateway` / `mirror` / `rewrite` / `script` / `reverse_proxy` 六族是**同一套 CRUD 模式**，只有 `access_control` / `network_throttling` / `secondary_proxy` / `ssl_proxying` / `report_server` 五族略瘦（没有 folder 或 list）。以 `rewrite` 为例：

```
capture_rewrite_get_config      # 当前配置（含总开关）
capture_rewrite_set_enabled     # 总开关
capture_rewrite_list            # 全部规则
capture_rewrite_set_item_enabled # 批量启停单条
capture_rewrite_get_by_id / capture_rewrite_create / capture_rewrite_update / capture_rewrite_delete
capture_rewrite_create_folder / capture_rewrite_delete_folder / capture_rewrite_update_folder_name
```

把 `rewrite` 换成 `breakpoint` / `gateway` / `mirror` / `script` / `reverse_proxy` 就是另外五族。
**顺序要点**：先 `*_get_config` 看总开关是否已开，再 `*_create`，最后 `*_set_enabled(true)` —— 只建规则不开总开关 = 规则不起作用。

## 3.5 登录前后的能力对照（2026-11-01 实测）

| 操作 | 未登录（本机当前状态） |
|---|---|
| `capture_live_set_enabled` / `status` / `clear` | ✅ |
| `capture_live_filter` / `get_by_id` / `generate_curl` | ✅ |
| `proxy_set` | ✅ |
| 各族 `*_get_config` / `*_list` / `*_lookup` / `*_get_active` | ✅ |
| 各族 `*_set_enabled`（功能总开关） | ✅（实测 `rewrite_set_enabled` 可用） |
| `script_framework` / `script_template` | ✅ |
| 各族 `*_create` 与 `*_update` / `*_delete` | ❌ 需登录账号 |
| `capture_live_compose` / `capture_live_collection_add` | ❌ 需登录账号 |
| `collection_*` / `environment_*` 的写操作 | ❌ 需登录账号 |

登录是**人在 GUI 里完成的动作**，Agent 不要代为登录、不要索取账号密码；未登录时按「只读 + 开关」规划工作流，并把写规则的需求交给 mitmdump 或人工。

## 4. 关键入参结构

### 断点 `capture_breakpoint_create`

```jsonc
{"name":"拦截下单","url":"api.example.com/order/*","wildcard":true,
 "method":"POST",              // 空串 = 任意方法
 "isRequestEnabled":true,      // 命中请求时暂停
 "isResponseEnabled":true,     // 命中响应时暂停
 "folderId":"..."}             // 可选
```

### 重写 `capture_rewrite_create`

`action.type` 取值（0–4）：

| type | 名称 | 用到的字段 |
|---|---|---|
| 0 | Redirect | `redirectUrl`、`preserveHost`、`excludeUrl`、`excludeWildcard` |
| 1 | Replace Request | `method`、`path`、`headers[]`、`body{}`、`requestLineEnabled`、`headersEnabled`、`bodyEnabled` |
| 2 | Replace Response | `code`、`headers[]`、`body{}`、`statusLineEnabled`、`headersEnabled`、`bodyEnabled` |
| 3 | Modify Request | `modifies[]`（见下） |
| 4 | Modify Response | `modifies[]` |

`body` 结构：`{"type":0|1|2,"payload":"..."}` —— 0=None（payload 空）、1=Text（文本）、2=Binary（**payload 是文件路径**）。

`modifies[]` 每项 `{id, type, modify, isEnabled}`，`type`：

| type | 动作 | `modify` 字段 |
|---|---|---|
| 0 | Modify Body | `pattern` / `replacement` / `regex` / `caseSensitive` |
| 1 | Add Query | `name` / `value` |
| 2 | Modify Query | `pattern` / `replacement` / `regex` / `caseSensitive` |
| 3 | Remove Query | `pattern1`（名字）/ `pattern2`（值）/ `regex1` / `regex2` |
| 4 | Add Header | `name` / `value` |
| 5 | Modify Header | `pattern` / `replacement` / `regex` / `caseSensitive` |
| 6 | Remove Header | `pattern1` / `pattern2` / `regex1` / `regex2` |

**注入异常的最短路径**：`type=2`（Replace Response）+ `code=500` 且 `statusLineEnabled=true`，或 `code=200` + `body.type=1` + 空数组 payload。

### 脚本 `capture_script_create`

```jsonc
{"name":"AES 解密","url":"api.example.com/*","wildcard":true,"code":"<Python>"}
```

⚠ `code` **必须先调 `script_framework` 和 `script_template` 拿到框架再写**，工具描述里明确要求。本机脚本目录 `%APPDATA%\Reqable\scripts`。

### 网络限速 `capture_network_throttling_create`

`{name, host (支持 * 和 ?), mode}`，另有 `*_get_active` / `*_select` 切换激活档位。慢网/3G 场景用它，别去改系统网络。

### 集合 `collection_api_create`

`{collectionId, parentId?, curl}` —— 由 cURL 建 API。集合功能需要登录 + 高级版。

## 5. `minimal` 缺什么

`minimal`（48 个）只覆盖：抓包列表 8 个中的常用 7 个、SSL 配置类全缺、代理开关、集合基础操作、脚本资源、REST 创建。
**缺**：断点 / 网关 / 镜像 / 重写 / 脚本规则的全部 CRUD（这些族的 `*_get_config`、`*_create`、`*_list` 都不在 minimal 里）、网络限速、反向代理、二级代理、访问控制、上报服务器、环境变量组。
→ **做逆向/改包一律 `--scope all`**。

## 6. 出错时的读法

- `Route not found.`（404）→ 路径不存在，通常是调了文档里没有的路由，或用了 GET 打只收 POST 的接口（`live/filter`、`live/get` 都只收 POST）。
- `filters is required`（400）→ `filters` 不是数组，或字段名写错。
- `Missing or invalid access token.`（401）→ `REQABLE_TOKEN` 没设 / 不匹配（见 local-environment.md）。
- 工具调用返回 `isError` 但模型看得懂 → 先把 `capture_live_status` 和 `proxy_set` 的真实状态打出来，再判断是不是 GUI 没起。
