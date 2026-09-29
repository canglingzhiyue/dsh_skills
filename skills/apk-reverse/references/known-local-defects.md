# 本机已知缺陷与未验证面（本机融合层）

> 本文件是**本机融合层**，不属于上游 `apk-reverse`；上游重新安装会覆盖技能目录，恢复时按账本一并还原。
> 用途：命中下列路线时**先做手工校验**，不要直接采信脚本输出。

## 1. 上游自认的两个活缺陷（会静默产出坏包）

### 1.1 `scripts\so_constpatch.py` 丢掉 zip `extra` 字段 → 破坏 4 KB 对齐

- 上游状态记录在 `docs\tool-verification\TOOL-VERDICTS.md`，措辞是 **"sealed, not fixed"**（记录了成因，但没修）。
- 影响面：重建后的 APK 里 native 库失去 4 KB 对齐；`extractNativeLibs="false"` 或对 `.so` 做等长补丁后的重打包最容易踩。
- 症状：安装被拒（常见 `INSTALL_FAILED_INVALID_APK` / `[-124]`），或装上后 native 崩溃——而且**其它校验看起来都通过**。
- 缓解（每次都要做）：
  ```powershell
  # 用本机 build-tools 36.1.0 校验对齐与 arsc 存储方式
  & 'D:\ProgramsDev\Android\SDK\build-tools\36.1.0\zipalign.exe' -c -p -v 4 <patched.apk>
  ```
  `resources.arsc` 必须 **STORED 且 4 字节对齐**；任何 `.so` 报未对齐就重做，不要抱侥幸。

### 1.2 `scripts\repack.py` 的 `_needs_alignment` 正则永远匹配不到

- 正则 `^lib/[^/]+\.so$` 只能匹配 `lib/x.so`，而真实路径是 `lib/arm64-v8a/x.so` —— **`.so` 对齐检测永远不会触发**。
- 上游记录见 `docs\tool-verification\EXTENSION-reconstruction.md`（"a live defect in `repack.py` … reported rather than fixed"）。
- 后果：`repack.py` 会报告"重建成功"，但产物可能未对齐。
- 缓解：**不采信它的自检结论**，一律用上面那条 `zipalign -c -p -v 4` 独立复核。

## 2. 上游从未端到端演练的路线（本机同样没有）

上游 `evidence\known-limitations.md` 明确列出：**packer（加固脱壳）、code-virtualization（VMP）、custom-linker、integrity-check-redirection、tamper-suicide** 这几条路线
"were never run end to end"，原因是首个验证样本的未修改版本身就无法启动。

→ 本机对这些路线**同样零实测**。按验收纪律（`reverse-skill-router` §5）要求：
- 结论必须标注 `unverified`，不得写成"该方法可用"；
- 首次真跑时，把它当作**新的验证任务**：建 case、留 control build、记录 time-to-death，成功后再把结论写回。

## 3. 从未执行过的评测集

`skills\apk-reverse\evals\evals.json` 自述：
```json
"_status": "unverified -- skeleton only",
"_warning": "NOTHING IN THIS FILE HAS EVER BEEN EXECUTED. … Do not cite this file as a quality measurement."
```
→ **不要引用它作为质量证据**；也不要因为它在 CI 里就以为跑过（上游 `ci.yml` 明确写了不跑 evals）。

## 4. 依赖不随技能交付

| 上游路线 | 缺的依赖 | 本机现状 |
|---|---|---|
| Dart AOT / Flutter | `aotopsy` 或 `blutter`（仓库不含），且两者对同一样本报不同 Dart 版本标签、偏移空间不一致 | 未安装 |
| recon 索引器 | `droidasc` / `ddc` | 未安装 → 用 jadx MCP 替代（见 `local-environment.md` §2） |
| 动态调试 | 设备侧 `frida-server`（匹配版本） | 本机无 `frida` CLI，只有 WMPFDebugger 的 Node 绑定 |
| 重打包 | `apktool` | **未安装** → 走 `scripts\repack.py` + §1 的独立对齐校验 |

## 5. 使用纪律

1. 命中 §1 的任一脚本 → 产物必须过 `zipalign -c -p -v 4` 与 `apksigner verify` 双检。
2. 命中 §2 的路线 → 先按"未验证"开工，别引用上游结论当既成事实。
3. 发现**新的**本机缺陷 → 追加到本文件（含症状 / 成因 / 缓解命令），不要只写在 journal 里。
