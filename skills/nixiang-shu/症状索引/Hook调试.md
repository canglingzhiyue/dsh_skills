# 症状索引 · Hook调试

> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。
> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；越低说明多条规则共用，需结合上下文判。
> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。

| 权重 | 症状（短语） | 报错原文 | 去哪 |
|---|---|---|---|
| 1.00 | 不知该改哪一层 |  | [hook-001](../references/Hook调试.md#hook-001) |
| 1.00 | jadx 里只有壳类 |  | [hook-002](../references/Hook调试.md#hook-002) |
| 1.00 | hook 挂上了没打印 |  | [hook-003](../references/Hook调试.md#hook-003) |
| 1.00 | attach 后拦不到 |  | [hook-003](../references/Hook调试.md#hook-003) |
| 1.00 | IDA 搜不到目标函数 |  | [hook-004](../references/Hook调试.md#hook-004) |
| 1.00 | 照老教程装的框架不生效 |  | [hook-005](../references/Hook调试.md#hook-005) |
| 1.00 | 模块列表显示未启用 |  | [hook-005](../references/Hook调试.md#hook-005) |
| 1.00 | hook 不生效但类已加载 |  | [hook-006](../references/Hook调试.md#hook-006) |
| 1.00 | findClass 报找不到类 |  | [hook-006](../references/Hook调试.md#hook-006) |
| 1.00 | native 方法找不到实现 |  | [hook-007](../references/Hook调试.md#hook-007) |
| 1.00 | 不知加密在哪个 so |  | [hook-007](../references/Hook调试.md#hook-007) |
| 1.00 | RegisterNatives 与 dlsym 全空 |  | [hook-008](../references/Hook调试.md#hook-008) |
| 1.00 | 注册在 attach 前完成 |  | [hook-008](../references/Hook调试.md#hook-008) |
| 1.00 | 换版本 hook 全失效 |  | [hook-009](../references/Hook调试.md#hook-009) |
| 1.00 | 别的机型就崩 |  | [hook-009](../references/Hook调试.md#hook-009) |
| 1.00 | hook dlopen 一点输出没有 |  | [hook-010](../references/Hook调试.md#hook-010) |
| 1.00 | so 加载时机抓不到 |  | [hook-010](../references/Hook调试.md#hook-010) |
| 1.00 | 手写 hook 模板太慢 |  | [hook-011](../references/Hook调试.md#hook-011) |
| 1.00 | 类太多不知从哪下手 |  | [hook-011](../references/Hook调试.md#hook-011) |
| 1.00 | 检测代码找不到 |  | [hook-012](../references/Hook调试.md#hook-012) |
| 1.00 | 静态搜不到 kill/ptrace |  | [hook-012](../references/Hook调试.md#hook-012) |
| 1.00 | AIDL 代理拦不到 |  | [hook-013](../references/Hook调试.md#hook-013) |
| 1.00 | 私有服务 hook 不到 |  | [hook-013](../references/Hook调试.md#hook-013) |
| 1.00 | IDA 的 XREF 全是空 |  | [hook-014](../references/Hook调试.md#hook-014) |
| 1.00 | 函数地址藏在参数里 |  | [hook-014](../references/Hook调试.md#hook-014) |
| 1.00 | hook 报重载歧义 |  | [hook-015](../references/Hook调试.md#hook-015) |
| 1.00 | 只在一部分场景生效 |  | [hook-015](../references/Hook调试.md#hook-015) |
| 1.00 |  | `has more than one overload` | [hook-015](../references/Hook调试.md#hook-015) |
| 1.00 |  | `argument types could not be found` | [hook-015](../references/Hook调试.md#hook-015) |
| 1.00 | 改了返回值没效果 |  | [hook-016](../references/Hook调试.md#hook-016) |
| 1.00 | 参数赋数值目标没变化 |  | [hook-016](../references/Hook调试.md#hook-016) |
| 1.00 | hook 后卡死或栈溢出 |  | [hook-017](../references/Hook调试.md#hook-017) |
| 1.00 | 一上钩就崩 |  | [hook-017](../references/Hook调试.md#hook-017) |
| 1.00 |  | `StackOverflowError` | [hook-017](../references/Hook调试.md#hook-017) |
| 1.00 | 改一处只部分生效 |  | [hook-018](../references/Hook调试.md#hook-018) |
| 1.00 | 值对了界面还不对 |  | [hook-018](../references/Hook调试.md#hook-018) |
| 1.00 | 当时能用后来随机退出 |  | [hook-019](../references/Hook调试.md#hook-019) |
| 1.00 | 换版本又要重改 |  | [hook-019](../references/Hook调试.md#hook-019) |
| 1.00 | 已去特征仍被检测退出 |  | [hook-020](../references/Hook调试.md#hook-020) |
| 1.00 | 清完常见特征还是被杀 |  | [hook-020](../references/Hook调试.md#hook-020) |
| 1.00 | 装框架就闪退 |  | [hook-021](../references/Hook调试.md#hook-021) |
| 1.00 | 停用模块仍然打不开 |  | [hook-021](../references/Hook调试.md#hook-021) |
| 1.00 | 自己算的和抓包不一致 |  | [hook-022](../references/Hook调试.md#hook-022) |
| 1.00 | 算法看着对但请求失败 |  | [hook-022](../references/Hook调试.md#hook-022) |
| 0.50 | 改完没生效 |  | [hook-001](../references/Hook调试.md#hook-001) |
| 0.50 | hook 报找不到类 |  | [hook-002](../references/Hook调试.md#hook-002) |
| 0.50 | native 声明找不到实现 |  | [hook-004](../references/Hook调试.md#hook-004) |
| 0.33 |  | `java.lang.ClassNotFoundException` | [hook-002](../references/Hook调试.md#hook-002) |
| 0.33 |  | `java.lang.ClassNotFoundException` | [hook-006](../references/Hook调试.md#hook-006) |
