# 症状索引 · VMP还原

> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。
> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；越低说明多条规则共用，需结合上下文判。
> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。

| 权重 | 症状（短语） | 报错原文 | 去哪 |
|---|---|---|---|
| 1.00 | 不确定是不是VMP |  | [vmp-001](../references/VMP还原.md#vmp-001) |
| 1.00 | 看不懂 so 入口 |  | [vmp-001](../references/VMP还原.md#vmp-001) |
| 1.00 | 照教程做完全失效 |  | [vmp-002](../references/VMP还原.md#vmp-002) |
| 1.00 | 换样本脚本无效 |  | [vmp-002](../references/VMP还原.md#vmp-002) |
| 1.00 | 还原很久只为拿一次结果 |  | [vmp-003](../references/VMP还原.md#vmp-003) |
| 1.00 | 结果只在运行时有效 |  | [vmp-003](../references/VMP还原.md#vmp-003) |
| 1.00 | IDA 没有具名节 |  | [vmp-004](../references/VMP还原.md#vmp-004) |
| 1.00 | init_array 找不到 |  | [vmp-004](../references/VMP还原.md#vmp-004) |
| 1.00 |  | `Section header not found` | [vmp-004](../references/VMP还原.md#vmp-004) |
| 1.00 | 怀疑自研加密 |  | [vmp-005](../references/VMP还原.md#vmp-005) |
| 1.00 | hash 对不上 |  | [vmp-005](../references/VMP还原.md#vmp-005) |
| 1.00 | so 搜不到 Java_ 函数 |  | [vmp-006](../references/VMP还原.md#vmp-006) |
| 1.00 | JS 里找不到加密入口 |  | [vmp-007](../references/VMP还原.md#vmp-007) |
| 1.00 | 整站 JS 只有一个巨型函数 |  | [vmp-007](../references/VMP还原.md#vmp-007) |
| 1.00 | 按教程建的解释器对不上 |  | [vmp-010](../references/VMP还原.md#vmp-010) |
| 1.00 | 操作数取值一直错 |  | [vmp-010](../references/VMP还原.md#vmp-010) |
| 1.00 | opcode 与操作数分不开 |  | [vmp-011](../references/VMP还原.md#vmp-011) |
| 1.00 | 字节码切分差一 |  | [vmp-011](../references/VMP还原.md#vmp-011) |
| 1.00 | trace 一开就卡死 |  | [vmp-014](../references/VMP还原.md#vmp-014) |
| 1.00 | 日志文件几百 MB |  | [vmp-014](../references/VMP还原.md#vmp-014) |
| 1.00 |  | `exception in thread` | [vmp-014](../references/VMP还原.md#vmp-014) |
| 1.00 |  | `OutOfMemory` | [vmp-014](../references/VMP还原.md#vmp-014) |
| 1.00 | 开了 trace 结果就变了 |  | [vmp-015](../references/VMP还原.md#vmp-015) |
| 1.00 | 装上 hook 就起不来 |  | [vmp-015](../references/VMP还原.md#vmp-015) |
| 1.00 | 同一地址改了却没生效 |  | [vmp-016](../references/VMP还原.md#vmp-016) |
| 1.00 | 只执行旧指令 |  | [vmp-016](../references/VMP还原.md#vmp-016) |
| 1.00 | 日志太多看不出主线 |  | [vmp-017](../references/VMP还原.md#vmp-017) |
| 1.00 | 不知插什么 |  | [vmp-017](../references/VMP还原.md#vmp-017) |
| 1.00 | 日志撒了一地也没看懂 |  | [vmp-018](../references/VMP还原.md#vmp-018) |
| 1.00 | 控制台滚动条滚不完 |  | [vmp-018](../references/VMP还原.md#vmp-018) |
| 1.00 | 文档说是 HMAC-SHA1 但算不对 |  | [vmp-020](../references/VMP还原.md#vmp-020) |
| 1.00 | 结构和标准算法一模一样 |  | [vmp-020](../references/VMP还原.md#vmp-020) |
| 1.00 | 表达式一堆位运算看不懂 |  | [vmp-021](../references/VMP还原.md#vmp-021) |
| 1.00 | 一处错导致全盘皆错 |  | [vmp-021](../references/VMP还原.md#vmp-021) |
| 1.00 | IR 里的值对不上 |  | [vmp-022](../references/VMP还原.md#vmp-022) |
| 1.00 | 折叠后结果偏移 |  | [vmp-022](../references/VMP还原.md#vmp-022) |
| 1.00 | 反混淆脚本越写越大 |  | [vmp-024](../references/VMP还原.md#vmp-024) |
| 1.00 | 永远收不了尾 |  | [vmp-024](../references/VMP还原.md#vmp-024) |
| 1.00 | 本地值算对了但线上不通 |  | [vmp-026](../references/VMP还原.md#vmp-026) |
| 1.00 | 重放就失败 |  | [vmp-026](../references/VMP还原.md#vmp-026) |
| 1.00 | 在自己挑的样本上对 |  | [vmp-027](../references/VMP还原.md#vmp-027) |
| 1.00 | 换个入口就不对 |  | [vmp-027](../references/VMP还原.md#vmp-027) |
| 1.00 | handler 看完不知操作数在哪 |  | [vmp-008](../待验证/VMP还原.md#vmp-008) `孤例` |
| 1.00 | handler 边界切不准 |  | [vmp-009](../待验证/VMP还原.md#vmp-009) `孤例` |
| 1.00 | 反编译只出前几行 |  | [vmp-012](../待验证/VMP还原.md#vmp-012) `孤例` |
| 1.00 | 间接跳转目标算不出来 |  | [vmp-013](../待验证/VMP还原.md#vmp-013) `孤例` |
| 1.00 | 按特征识别出的语义对不上 |  | [vmp-019](../待验证/VMP还原.md#vmp-019) `孤例` |
| 1.00 | 返回值时对时错 |  | [vmp-023](../待验证/VMP还原.md#vmp-023) `孤例` |
| 1.00 | IDA 里函数标红无返回 |  | [vmp-025](../待验证/VMP还原.md#vmp-025) `孤例` |
| 1.00 | 补丁打了像没生效 |  | [vmp-028](../待验证/VMP还原.md#vmp-028) `孤例` |
| 1.00 | 一断点就走错分支 |  | [vmp-029](../待验证/VMP还原.md#vmp-029) `孤例` |
| 0.50 | native 声明找不到实现 |  | [vmp-006](../references/VMP还原.md#vmp-006) |
