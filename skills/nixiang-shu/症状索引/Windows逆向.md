# 症状索引 · Windows逆向

> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。
> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；越低说明多条规则共用，需结合上下文判。
> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。

| 权重 | 症状（短语） | 报错原文 | 去哪 |
|---|---|---|---|
| 1.00 | 不确定有没有加壳 |  | [win-001](../references/Windows逆向.md#win-001) |
| 1.00 | 导入表只剩几项 |  | [win-001](../references/Windows逆向.md#win-001) |
| 1.00 | 分不清是壳还是 .NET |  | [win-002](../references/Windows逆向.md#win-002) |
| 1.00 | IDA 里全是解析不出的代码 |  | [win-002](../references/Windows逆向.md#win-002) |
| 1.00 | 不知道是什么语言写的 |  | [win-003](../references/Windows逆向.md#win-003) |
| 1.00 | 反编译看不懂调用约定 |  | [win-003](../references/Windows逆向.md#win-003) |
| 1.00 | 搜不到成功或失败提示 |  | [win-004](../references/Windows逆向.md#win-004) |
| 1.00 | 有弹窗却搜不到那串文本 |  | [win-004](../references/Windows逆向.md#win-004) |
| 1.00 | 不知道该脱壳还是该逆算法 |  | [win-005](../references/Windows逆向.md#win-005) |
| 1.00 | 注册码改了没用 |  | [win-005](../references/Windows逆向.md#win-005) |
| 1.00 | 本地改完请求仍被拒 |  | [win-006](../references/Windows逆向.md#win-006) |
| 1.00 | 改了会员标识服务端不认 |  | [win-006](../references/Windows逆向.md#win-006) |
| 1.00 | 弹 Themida 提示却根本进不去 |  | [win-007](../references/Windows逆向.md#win-007) |
| 1.00 | 按某壳流程脱一半卡住 |  | [win-007](../references/Windows逆向.md#win-007) |
| 1.00 |  | `can't run under virtual machine` | [win-007](../references/Windows逆向.md#win-007) |
| 1.00 | UPX/ASPack 脱完跑不起来 |  | [win-008](../references/Windows逆向.md#win-008) |
| 1.00 | 不知道 OEP 在哪 |  | [win-008](../references/Windows逆向.md#win-008) |
| 1.00 | 壳代码全是运算看不懂 |  | [win-009](../references/Windows逆向.md#win-009) |
| 1.00 | VMP 里找不到业务入口 |  | [win-009](../references/Windows逆向.md#win-009) |
| 1.00 | dump 出来是乱码 |  | [win-010](../references/Windows逆向.md#win-010) |
| 1.00 | dll 拿不到解密后的内容 |  | [win-010](../references/Windows逆向.md#win-010) |
| 1.00 | 不知道校验在哪 |  | [win-011](../references/Windows逆向.md#win-011) |
| 1.00 | 主函数太长跟不下去 |  | [win-011](../references/Windows逆向.md#win-011) |
| 1.00 | OllyDbg 在新系统上跑不动 |  | [win-012](../references/Windows逆向.md#win-012) |
| 1.00 | OD 里没伪代码也导不出 trace |  | [win-012](../references/Windows逆向.md#win-012) |
| 1.00 | 断在 strcmp 只看到结果 |  | [win-013](../references/Windows逆向.md#win-013) |
| 1.00 | 拿不到密钥 |  | [win-013](../references/Windows逆向.md#win-013) |
| 1.00 | 断点还没到进程就退出 |  | [win-014](../references/Windows逆向.md#win-014) |
| 1.00 | 随便一动就被杀 |  | [win-014](../references/Windows逆向.md#win-014) |
| 1.00 | 哈希怎么反推 |  | [win-015](../references/Windows逆向.md#win-015) |
| 1.00 | 要不要把算法完全还原 |  | [win-015](../references/Windows逆向.md#win-015) |
| 1.00 | 长度固定却对不上 |  | [win-016](../references/Windows逆向.md#win-016) |
| 1.00 | 分段校验拼不起来 |  | [win-016](../references/Windows逆向.md#win-016) |
| 1.00 | 改完能启动过一会失效 |  | [win-017](../references/Windows逆向.md#win-017) |
| 1.00 | 重新签名就被拦 |  | [win-017](../references/Windows逆向.md#win-017) |
| 1.00 | 改了校验函数别处崩 |  | [win-018](../references/Windows逆向.md#win-018) |
| 1.00 | 改了没效果 |  | [win-018](../references/Windows逆向.md#win-018) |
| 1.00 | 改成立刻被别处发现 |  | [win-019](../references/Windows逆向.md#win-019) |
| 1.00 | 改了结果引出副作用 |  | [win-019](../references/Windows逆向.md#win-019) |
| 1.00 | 不知道改内存还是改文件 |  | [win-020](../references/Windows逆向.md#win-020) |
| 1.00 | 重打包后一堆功能坏 |  | [win-020](../references/Windows逆向.md#win-020) |
| 1.00 | dump 出来 IDA 打不开 |  | [win-021](../references/Windows逆向.md#win-021) |
| 1.00 | 节表对不上文件大小 |  | [win-021](../references/Windows逆向.md#win-021) |
| 1.00 | 一次改很多处对不上原因 |  | [win-022](../references/Windows逆向.md#win-022) |
| 1.00 | 定位不到是哪处生效 |  | [win-022](../references/Windows逆向.md#win-022) |
| 1.00 | 改 IL 字节后程序集加载失败 |  | [win-023](../references/Windows逆向.md#win-023) |
| 1.00 | 强命名 dll 改不了 |  | [win-023](../references/Windows逆向.md#win-023) |
| 1.00 | VB 里全是看不懂的 call |  | [win-024](../references/Windows逆向.md#win-024) |
| 1.00 | 反编译出来是伪代码 |  | [win-024](../references/Windows逆向.md#win-024) |
| 1.00 | Delphi 函数名看不懂 |  | [win-025](../references/Windows逆向.md#win-025) |
| 1.00 | 消息循环里找不到校验 |  | [win-025](../references/Windows逆向.md#win-025) |
| 1.00 | hook 装上了函数照常返回原值 |  | [win-026](../references/Windows逆向.md#win-026) |
| 1.00 | 注入成功但毫无效果 |  | [win-026](../references/Windows逆向.md#win-026) |
| 1.00 | 换台机器偏移全废 |  | [win-027](../references/Windows逆向.md#win-027) |
| 1.00 | 脚本里的地址下次就不对 |  | [win-027](../references/Windows逆向.md#win-027) |
| 1.00 | 算出的码本机能用换机不行 |  | [win-028](../references/Windows逆向.md#win-028) |
| 1.00 | 一组过了就交付 |  | [win-028](../references/Windows逆向.md#win-028) |
| 1.00 | 标题显示已注册但功能还限制 |  | [win-029](../references/Windows逆向.md#win-029) |
| 1.00 | 跑一会静默退回原行为 |  | [win-029](../references/Windows逆向.md#win-029) |
