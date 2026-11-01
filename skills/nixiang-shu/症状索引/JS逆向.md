# 症状索引 · JS逆向

> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。
> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；越低说明多条规则共用，需结合上下文判。
> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。

| 权重 | 症状（短语） | 报错原文 | 去哪 |
|---|---|---|---|
| 1.00 | 复现结果与线上不一致 |  | [jsfx-001](../references/JS逆向.md#jsfx-001) |
| 1.00 | 换参数就复现不了 |  | [jsfx-001](../references/JS逆向.md#jsfx-001) |
| 1.00 | JS 里搜不到目标串 |  | [jsfx-002](../references/JS逆向.md#jsfx-002) |
| 1.00 | 改了前端毫无反应 |  | [jsfx-002](../references/JS逆向.md#jsfx-002) |
| 1.00 | 搜 sign 命中几百处 |  | [jsfx-003](../references/JS逆向.md#jsfx-003) |
| 1.00 | 改的函数是死代码 |  | [jsfx-003](../references/JS逆向.md#jsfx-003) |
| 1.00 | 混淆代码读不懂 |  | [jsfx-004](../references/JS逆向.md#jsfx-004) |
| 1.00 | 不知该清字符串还是插桩 |  | [jsfx-004](../references/JS逆向.md#jsfx-004) |
| 1.00 | 同一请求复现结果不同 |  | [jsfx-005](../references/JS逆向.md#jsfx-005) |
| 1.00 | 偶尔对偶尔错 |  | [jsfx-005](../references/JS逆向.md#jsfx-005) |
| 1.00 | 搜 sign/encrypt 全是死代码 |  | [jsfx-006](../references/JS逆向.md#jsfx-006) |
| 1.00 | 待签串搜不到 |  | [jsfx-006](../references/JS逆向.md#jsfx-006) |
| 1.00 | 日志几十万条读不完 |  | [jsfx-007](../references/JS逆向.md#jsfx-007) |
| 1.00 | 插桩后更看不懂 |  | [jsfx-007](../references/JS逆向.md#jsfx-007) |
| 1.00 | 64 位不知道是什么 |  | [jsfx-008](../references/JS逆向.md#jsfx-008) |
| 1.00 | 试算对不上 |  | [jsfx-008](../references/JS逆向.md#jsfx-008) |
| 1.00 | 找不到加密点 |  | [jsfx-009](../references/JS逆向.md#jsfx-009) |
| 1.00 | 断点打不到关键帧 |  | [jsfx-009](../references/JS逆向.md#jsfx-009) |
| 1.00 | 插桩日志全是噪声 |  | [jsfx-010](../references/JS逆向.md#jsfx-010) |
| 1.00 | 不知道插哪儿 |  | [jsfx-010](../references/JS逆向.md#jsfx-010) |
| 1.00 | dispatch 读不懂 |  | [jsfx-011](../references/JS逆向.md#jsfx-011) |
| 1.00 | 想跳过解混淆直接拿指令 |  | [jsfx-011](../references/JS逆向.md#jsfx-011) |
| 1.00 | 手改插桩就崩 |  | [jsfx-012](../references/JS逆向.md#jsfx-012) |
| 1.00 | 索引取值丢了 |  | [jsfx-012](../references/JS逆向.md#jsfx-012) |
| 1.00 | handler 几百个读不完 |  | [jsfx-013](../references/JS逆向.md#jsfx-013) |
| 1.00 | 不知该看哪段变换 |  | [jsfx-013](../references/JS逆向.md#jsfx-013) |
| 1.00 | base64 解出来是乱码 |  | [jsfx-014](../references/JS逆向.md#jsfx-014) |
| 1.00 | 不报错但结果不对 |  | [jsfx-014](../references/JS逆向.md#jsfx-014) |
| 1.00 | 怀疑 MD5/SHA-1 被魔改 |  | [jsfx-015](../references/JS逆向.md#jsfx-015) |
| 1.00 | 不知道改了几处 |  | [jsfx-015](../references/JS逆向.md#jsfx-015) |
| 1.00 | 反复进 debugger |  | [jsfx-016](../references/JS逆向.md#jsfx-016) |
| 1.00 | 分不清检测还是自己错 |  | [jsfx-016](../references/JS逆向.md#jsfx-016) |
| 1.00 | 补了很久环境仍不通 |  | [jsfx-017](../references/JS逆向.md#jsfx-017) |
| 1.00 | 不报错但结果错 |  | [jsfx-017](../references/JS逆向.md#jsfx-017) |
| 1.00 | 美化后代码就出错 |  | [jsfx-018](../references/JS逆向.md#jsfx-018) |
| 1.00 | 格式化后被流控 |  | [jsfx-018](../references/JS逆向.md#jsfx-018) |
| 1.00 | 补了几十项仍跑不通 |  | [jsfx-019](../references/JS逆向.md#jsfx-019) |
| 1.00 | node 里报未定义 |  | [jsfx-019](../references/JS逆向.md#jsfx-019) |
| 1.00 | 环境补齐但仍被静默判死 |  | [jsfx-020](../references/JS逆向.md#jsfx-020) |
| 1.00 | 指纹混进参数 |  | [jsfx-020](../references/JS逆向.md#jsfx-020) |
| 1.00 | hook 挂上被反制 |  | [jsfx-021](../references/JS逆向.md#jsfx-021) |
| 1.00 | 检测照常触发 |  | [jsfx-021](../references/JS逆向.md#jsfx-021) |
| 1.00 | 能跑出值但不敢确定 |  | [jsfx-023](../references/JS逆向.md#jsfx-023) |
| 1.00 | 上线后服务端不认 |  | [jsfx-023](../references/JS逆向.md#jsfx-023) |
| 1.00 | 拿到 token 但业务不通 |  | [jsfx-024](../references/JS逆向.md#jsfx-024) |
| 1.00 | 登录仍失败 |  | [jsfx-024](../references/JS逆向.md#jsfx-024) |
| 1.00 | 工具报出了结果 |  | [jsfx-025](../references/JS逆向.md#jsfx-025) |
| 1.00 | 结果与密文对不上 |  | [jsfx-025](../references/JS逆向.md#jsfx-025) |
| 1.00 | 不知从哪个关键词下手 |  | [jsfx-026](../references/JS逆向.md#jsfx-026) |
| 1.00 | 换版本全失效 |  | [jsfx-026](../references/JS逆向.md#jsfx-026) |
| 1.00 | wasm 搜不到串 |  | [jsfx-027](../references/JS逆向.md#jsfx-027) |
| 1.00 | f12 打不开 wasm |  | [jsfx-027](../references/JS逆向.md#jsfx-027) |
| 1.00 | 轨迹被判为机器 |  | [jsfx-028](../references/JS逆向.md#jsfx-028) |
| 1.00 | 调参数越调越差 |  | [jsfx-028](../references/JS逆向.md#jsfx-028) |
| 1.00 | 改了文件页面毫无变化 |  | [jsfx-022](../待验证/JS逆向.md#jsfx-022) `孤例` |
