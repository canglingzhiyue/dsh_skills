---
name: nixiang-zhengliu
description: 逆向经验语料蒸馏引擎 —— 把「采集提炼好的经验笔记库」蒸馏成 nixiang-shu 技能树节点（规则草案 + 证据计数 + 渲染 + 三闸门自检）。当需要新增语料库、给技能树加主题、或对既有主题做增删改（新经验入树 / 证伪的规则退役）时使用。触发：蒸馏语料、把笔记变成技能、扩充技能树、新增主题、退役过时规则。
---

# nixiang-zhengliu —— 蒸馏引擎

**它是一个引擎，不是知识**。知识在 `nixiang-shu`（树）里；本技能负责"把任意语料库变成树的节点"，并且**自带修正能力**。

## 0. 三个事实源

| 事实源 | 位置 | 谁产生 |
|---|---|---|
| 树（产物） | `$DSH_HOME\skills\nixiang-shu\` | 本引擎渲染输出 |
| 引擎脚本 | 本技能 `scripts\`（快照自案件库） | 本引擎自带 |
| 规则 schema | `references\rule-schema.md` | 人工维护，改格式=升版本号 |

## 1. 跑法契约（换语料库只改这一处）

```
输入 = 语料库路径 + 笔记 schema（8 节结构）+ 主题名 + id 前缀
输出 = <主题>.rules.json → 证据化 → 渲染 → 三闸门报告
```

**唯一的配置点是 `scripts\common.py` 顶部的路径常量**：

```python
LIB_52PJ = Path(r"D:\AI_python\reverse\52pojie")   # 换语料库改这里
LIB_KX   = Path(r"D:\AI_python\reverse\kanxue")
CASE_ROOT = Path(r"D:\AI_python\reverse-cases\2026-11-01_skills-distill")  # 中间产物落处
```

## 2. 五步流程

| 步 | 命令 | 产出 | 通过标准 |
|---|---|---|---|
| ① 提炼 | 派 subagent，提示词见 `references\extract-prompt.md` | `<主题>.rules.json` | 条数 15–45、必填 0 缺失、渲染 ≤11,000 |
| ② 证据化 | `uv run --no-project python scripts\build_evidence_index.py` | `<主题>.evidence.json` | 每条有 level/锚点/旁证 |
| ③ 渲染 | `python scripts\render_tree.py` | 树文件 | 输出无截断 WARN |
| ④ 预算闸门 | `python scripts\check_budget.py` | OK/FAIL | **必须 OK** |
| ⑤ 链接闸门 | `python scripts\check_links.py` | OK/FAIL | **必须 OK** |
| ⑥ 回归 | `python scripts\run_cases.py` | 基线/PASS | 冻结后必须 PASS |

跑之前统一设：
```powershell
$env:UV_CACHE_DIR="$env:TEMP\nz-cache"; $env:PYTHONIOENCODING='utf-8'
```

## 3. 证据分级（这套引擎的核心，别搞错）

```
基线 = 提炼者声明的 anchors 数：≥3 strong ｜ 2 weak ｜ ≤1 single
上限 = min(基线, evidence_hint)          ← 提炼者说孤例就是孤例，不许被锚点数洗成 strong
升级 = 孤例 + ≥3 条高分旁证(≥0.35) + 跨库 → weak（仅此一种升级）
封顶 = anchors 里有 hard_gap / md_empty，或规则自述 img_dependent → 最高 weak
```

⚠ **证据等级 = 人审锚点 + 旁证，不是关键词检索召回**。检索只给线索，不给结论。

## 4. 自扩展（新经验入树）

1. 新经验先写进案件库 `journal.md`，**不直接改树**；
2. 达到门槛才提议：**同案直接观察到 ≥1 次 + 有 control build 对照**；
3. 孤例只能进 `待验证\`，进不了主树；
4. 落地 = 改草案 JSON → 重跑 ②③④⑤⑥，**不许绕过闸门**。

## 5. 自修复（证伪的规则退役）

1. 触发门槛：**≥2 个独立案件证伪**，或**本机实测工具/接口已不存在**；
2. **不硬删**：移进 `待验证\` 或 `已失效.md`，写清失效原因、证据锚点、判定日期；
3. 对应回归用例必须**显式改写**（那条规则被退役了），而不是让它悄悄 FAIL；
4. 重跑闸门，journal 记一行。

## 6. 已知教训（踩过的，别再踩）

| 教训 | 后果 | 对策 |
|---|---|---|
| 只卡单文件不卡主题合计 | 主题合计超预算 48% 却全过，闸门形同虚设 | `check_budget` 已加合计闸门 |
| `#rule-id` 当锚点 | 真实 Markdown 里跳不过去，闸门却永远 PASS | 渲染时插 `<a id>`，闸门只认 `<a id>` |
| 拆分反而更超预算 | 每份重付页头，多出 1,131 字符 | 拆分留余量；子文件用极简页头 |
| 拆分后旧文件残留 | 主题合计虚高 2 倍 | 渲染脚本会打印清理命令，**必须执行** |
| 子代理按 12,000 设计 | 加证据行后全超预算返工 | 任务书写 **≤11,000**、每条约 380 字符 |
| 估算公式 | 高估/低估都发生过 | **只用真实渲染器量** |
| `Remove-ToRecycleBin.ps1` 批量删 | 不接受数组参数 | `foreach` 逐个调用 |
