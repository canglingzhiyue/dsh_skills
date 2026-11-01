---
name: nixiang-shu
description: 逆向树 —— 两库（52pojie 4999 篇 + 看雪 1485 篇）经验蒸馏成的判断链技能树。按症状查：脱壳闪退、重打包白屏、Hook 不生效、签名参数定位、加固版本判别、反调试对抗等。触发：卡住了、没思路、报错、闪退、装不上、脱壳、改包、Hook、签名、反调试、算法还原。
---

# nixiang-shu —— 逆向树

**这不是操作手册，是判断链。** 每条规则都是「看到什么 → 凭什么推断 → 所以做什么 → 不通换哪条」。

## 加载协议（照做，不要一次读完）

1. **先看症状索引** `症状索引.md`：拿你手上的现象（用户口吻）或报错原文去搜，命中即跳转。
2. **只读命中的那一个主题文件**：`references/<主题>.md`，读该规则的四行就够。
3. **锚点回查**：规则末尾的 tid 可回本地语料库查原文；跨机器时用 `锚点/<主题>.tsv` 里的 URL。
4. **走不通**：先看该规则的 `失效条件`，再看 `已失效.md`（墓碑），最后才考虑新开一条规则。
5. **本机工具事实**以 `$DSH_HOME\reverse\capabilities.md` 为准，不要相信笔记里写的工具版本。

## 主题路由表

| 主题 | 规则数 | 主题页 | 症状索引 |
|---|---|---|---|
| AI辅助 | 17 | [references/AI辅助.md](references/AI辅助.md) | [症状索引/AI辅助.md](症状索引/AI辅助.md) |
| Hook调试 | 22 | [references/Hook调试.md](references/Hook调试.md) | [症状索引/Hook调试.md](症状索引/Hook调试.md) |
| JS逆向 | 27 | [references/JS逆向.md](references/JS逆向.md) | [症状索引/JS逆向.md](症状索引/JS逆向.md) |
| VMP还原 | 20 | [references/VMP还原.md](references/VMP还原.md) | [症状索引/VMP还原.md](症状索引/VMP还原.md) |
| Web安全 | 19 | [references/Web安全.md](references/Web安全.md) | [症状索引/Web安全.md](症状索引/Web安全.md) |
| Windows逆向 | 29 | [references/Windows逆向.md](references/Windows逆向.md) | [症状索引/Windows逆向.md](症状索引/Windows逆向.md) |
| 协议抓包 | 28 | [references/协议抓包.md](references/协议抓包.md) | [症状索引/协议抓包.md](症状索引/协议抓包.md) |
| 小程序 | 10 | [references/小程序.md](references/小程序.md) | [症状索引/小程序.md](症状索引/小程序.md) |
| 改包会员 | 26 | [references/改包会员.md](references/改包会员.md) | [症状索引/改包会员.md](症状索引/改包会员.md) |
| 样本分析 | 5 | [references/样本分析.md](references/样本分析.md) | [症状索引/样本分析.md](症状索引/样本分析.md) |
| 游戏逆向 | 6 | [references/游戏逆向.md](references/游戏逆向.md) | [症状索引/游戏逆向.md](症状索引/游戏逆向.md) |
| 环境工具 | 28 | [references/环境工具.md](references/环境工具.md) | [症状索引/环境工具.md](症状索引/环境工具.md) |
| 算法还原 | 27 | [references/算法还原.md](references/算法还原.md) | [症状索引/算法还原.md](症状索引/算法还原.md) |
| 系统内核 | 23 | [references/系统内核.md](references/系统内核.md) | [症状索引/系统内核.md](症状索引/系统内核.md) |
| 综合实战 | 19 | [references/综合实战.md](references/综合实战.md) | [症状索引/综合实战.md](症状索引/综合实战.md) |
| 脱壳加固 | 24 | [references/脱壳加固.md](references/脱壳加固.md) | [症状索引/脱壳加固.md](症状索引/脱壳加固.md) |
| 静态分析 | 26 | [references/静态分析.md](references/静态分析.md) | [症状索引/静态分析.md](症状索引/静态分析.md) |

## 预算（由 `check_budget.py` 卡）

根 ≤6,000 字符 ｜ 单文件 ≤12,000 ｜ **主题合计 ≤11,000** ｜ 索引单份 ≤8,000、合计 ≤60,000 ｜ 全树 ≤200,000 字符 ｜ 单次加载 ≤30,000 字符。
拆文件不降低主题合计——超了必须**砍规则或压措辞**，不许靠「反正按需加载」糊过去。
