# 规则 schema —— 树的最小单元（v1，2026-11-01 定）

> 蒸馏产物的**唯一格式**。`build_evidence_index.py`、`check_budget.py`、`run_cases.py`、
> 以及以后 `nixiang-zhengliu` 的 diff 输出，全部以它为准。改字段 = 改这里的版本号。

## 一、文件层

一个主题一份草案：`output/drafts/<主题>.rules.json`

```json
{
  "schema_version": "v1",
  "theme": "脱壳加固",
  "source_handbooks": ["52pojie/docs/handbook/脱壳加固.md", "kanxue/docs/handbook/脱壳加固.md"],
  "generated_at": "2026-11-01",
  "rules": [ ... ]
}
```

## 二、规则节点字段

| 字段 | 必填 | 含义与写法 |
|---|---|---|
| `id` | 是 | `<主题拼音缩写>-<三位序号>`，如 `tuoke-001` |
| `title` | 是 | **一句话祈使句**规则，≤40 字。这是树的叶子节点标题 |
| `domain` | 是 | `android` / `web` / `windows` / `kernel` / `miniapp` / `sample` / `game` / `generic` |
| `stage` | 是 | `侦察` / `定位` / `校验` / `补丁` / `验证`（双轴矩阵的"阶段"轴） |
| `symptom` | 是 | 现象关键词数组（**症状索引的第一列**），写用户会怎么说的话，如 `"脱壳后装不上"`、`"重打包白屏"` |
| `error_patterns` | 否 | 精确报错原文（**症状索引的第二列**），如 `"Fatal signal 6"`、`"INSTALL_FAILED_UPDATE_INCOMPATIBLE"` |
| `judge` | 是 | 判断链：`看到 X → 推断 Y`。**这是 52pojie 笔记第 3 节和看雪手册"判断依据"的核心** |
| `action` | 是 | 具体做什么（可含命令/工具/参数，但**不写"针对某个 App 的成品步骤"**） |
| `if_not` | 是 | 无效时的下一步；没有就写 `无（无已知替代路径）` |
| `invalidate_when` | 是 | **失效条件**（必填，自修复的抓手）：什么情况下这条不再成立 |
| `keys` | 是 | 用于证据检索的技术指纹，4–12 个：工具名、API、文件名、报错码、十六进制特征 |
| `anchors` | 是 | 支撑该规则的 tid 列表（**只写 tid，不写摘要**）。`build_evidence_index.py` 会用它做交叉校验 |
| `evidence_hint` | 是 | 提炼者初判 `strong` / `weak` / `single`，**最终等级由检索覆盖** |
| `img_dependent` | 是 | `true` 表示关键判据在原帖截图里（会被压到 weak） |

## 三、写作硬规矩

1. **一条规则一件事**。看到"先 A 再 B"就拆成两条，用 `if_not` 串起来。
2. **不写成品步骤**：`action` 里不出现"改 com.xxx 的 payCallback 返回 true"这类针对具体产品的改法；
   这类内容只留锚点，回原帖看。
3. **`judge` 必须有因果**：写"看到 `libjiagu.so` 在 `assets` 里 → 是乐固 → 脱壳点看 `StubApp`"，
   不写"分析加固"（正确的废话）。
4. **`invalidate_when` 必须具体**：写"壳版本 ≥ 3.x 后 `StubApp` 不再是入口"，不写"版本更新后可能失效"。
5. **区分实测/推断/未验证**：本机没跑过的，在 `action` 末尾加 `【未验证】`。

## 四、预算（由 `check_budget.py` 卡）

| 文件 | 上限 |
|---|---|
| 该 JSON 渲染成 markdown 后 | ≤ 12,000 字符 |
| 单条规则渲染后 | ≤ 900 字符 |
| 规则条数/主题 | 15–45 条（少于 15 说明主题没榨干，多于 45 说明在写操作手册） |
