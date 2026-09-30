# 安装、配置与重建

## 1. 安装（本机已装，此处供换机重建）

```powershell
$p   = "http://127.0.0.1:7890"          # 本机访问 GitHub 走代理，直连会 Connection reset
$ver = "3.6.62"
$url = "https://github.com/Mouseww/anything-analyzer/releases/download/v3.6.61/Anything-Analyzer-Setup-$ver.exe"
$out = "$env:TEMP\Anything-Analyzer-Setup-$ver.exe"
Invoke-WebRequest -Uri $url -Proxy $p -OutFile $out

# 校验（v3.6.62 实测值）
(Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
#   ffe94c78df92a84d5ad347fa2938c0aec63775ce925c9cbac6ee3ad912c2c60c

# NSIS 静默安装；/D= 必须是最后一个参数且不能加引号
Start-Process -FilePath $out -ArgumentList "/S","/D=D:\ProgramsDev\AnythingAnalyzer" -Wait
```

> Release 的 tag 名与包内版本号不一致（tag `v3.6.61` 里装的是 `3.6.62`），下载 URL 用 tag，文件名用版本号。
> 资产列表：`https://github.com/Mouseww/anything-analyzer/releases/expanded_assets/<tag>`

安装后可执行文件：`D:\ProgramsDev\AnythingAnalyzer\Anything Analyzer.exe`
用户数据目录（用 package.json 的 `name`，**不是** productName）：`%APPDATA%\anything-analyzer\`

## 2. 配置文件（改完重启应用生效，不必点 GUI）

`%APPDATA%\anything-analyzer\mcp-server-config.json`
```json
{ "enabled": true, "host": "127.0.0.1", "port": 23816, "authEnabled": true, "authToken": "<uuid>" }
```
- `host` 出厂默认是 `0.0.0.0`（对局域网暴露）；**本机已改为 `127.0.0.1`**，MCP 只给本机 Agent 用，手机抓包走的是 MITM 的 8888，不受影响。
- `authToken` 留空时首次启动自动生成 UUID 并写回文件。**这是凭据，不写进任何 skill / 账本文本。**
- `enabled:false` 时 MCP 端口根本不监听。

`%APPDATA%\anything-analyzer\mitm-proxy-config.json`
```json
{ "enabled": true, "port": 8888, "caInstalled": false, "systemProxy": false }
```
- `systemProxy:false` —— **不动系统代理**（需要桌面应用/终端自动走代理时才设 true，会写 Windows 注册表）。
- `caInstalled` 只是界面状态标记，**不代表证书真的进了系统信任库**。

## 3. DSH MCP 挂载

写在 profile 的 `cordis.patch.yml`（本机：`C:\Users\y\.dsh\profiles\web\cordis.patch.yml`）：

```yaml
- insert:
    - id: mcp-anything-analyzer
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: analyzer
        transport: streamable-http
        url: 'http://127.0.0.1:23816/mcp'
        headers:
          Authorization: 'Bearer <authToken，取自 mcp-server-config.json>'
        toolCallTimeoutMs: 120000
        failOnStartupError: false
```

- 只有一个 StreamableHTTP 端点，**没有 stdio 模式**：MCP Server 依赖 Electron 的 `session` / `windowManager` / `AiAnalyzer`，不可能脱离 GUI 跑。
- `failOnStartupError: false` → GUI 没开时静默失效，**用 probe 脚本探活**。
- **改完要重启 DSH 才生效。**

## 4. CA 证书（HTTPS 抓包的前置，未完成）

证书文件：`%APPDATA%\anything-analyzer\certs\ca-cert.pem`
（同目录还有 `ca-key.pem` —— 私钥，别外传）

### 4.1 装到 Windows 系统信任库
GUI：Settings → MITM 代理 → 安装 CA 证书 → 弹 UAC。
等价命令（**需要管理员**）：
```powershell
certutil -addstore Root "$env:APPDATA\anything-analyzer\certs\ca-cert.pem"
# 卸载
certutil -delstore Root "Anything Analyzer CA"
```

> ⚠️ 这一步改动系统根证书信任库，属于系统级安全状态变更 —— **执行前须用户拍板**。
> 不装也能用：HTTP 流量、以及浏览器侧 CDP 抓包（CDP 走的是浏览器内部，不需要 MITM 证书）。

### 4.2 装到手机
1. 手机 Wi-Fi → 手动代理 → `<电脑局域网IP>:8888`
2. 手机浏览器打开 `http://<电脑局域网IP>/cert.cer`（DER 格式，最省事）
3. iOS：设置 → 已下载描述文件 → 安装 → **再到「关于本机 → 证书信任设置」里手动开启完全信任**（这步最容易漏）
4. Android：设置 → 安全 → 加密与凭据 → 从存储安装 → **CA 证书**

### 4.3 Android 7+ 的关键限制
**Android 7 起，App 默认不信任用户安装的证书**（只信任系统 CA）。所以装完 CA 后：
- 浏览器 / H5 页面：能抓 ✅
- App 自身流量：**抓不到，握手会失败** ❌

三条出路：
1. **设备 root 后把证书塞进系统存储**（本机真机 MI_8_SE 是 Magisk —— 用 Magisk 模块或 `adb push` 到 `/system/etc/security/cacerts/`，文件名须是 `<旧式hash>.0`）。**首选**。
2. App 的 `networkSecurityConfig` 若声明了信任用户证书（`<certificates src="user"/>`），则用户证书可用。
3. 上 Frida 绕过 SSL pinning + 自写 mitm 脚本 —— 那是 `apk-reverse` 的地盘。

## 5. 升级

自动更新（electron-updater）会在启动 3 秒后检查 GitHub。
升级后需重做：
1. 重跑 `scripts\probe-mcp.ps1` 确认 30 个工具还在（工具面随版本变）；
2. 检查 `mcp-server-config.json` 是否被重置（`enabled` 可能回 false）；
3. UA 里的版本串会变，skill 中「UA 暴露工具名」那条的示例值需同步。

## 6. 卸载 / 回退

```powershell
# 走回收站，别硬删（dev-hygiene）
& "$env:USERPROFILE\.dsh\skills\dev-hygiene\scripts\Remove-ToRecycleBin.ps1" -Path "D:\ProgramsDev\AnythingAnalyzer"
```
另有 `Uninstall Anything Analyzer.exe`（安装目录内）。
系统信任库里的 CA 用 `certutil -delstore Root "Anything Analyzer CA"`（管理员）。
DSH 侧回退：删掉 `cordis.patch.yml` 里 `mcp-anything-analyzer` 那个 insert 块，重启 DSH。
