# 症状索引 · Web安全

> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。
> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；越低说明多条规则共用，需结合上下文判。
> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。

| 权重 | 症状（短语） | 报错原文 | 去哪 |
|---|---|---|---|
| 1.00 | sign 参数看不懂不敢动 |  | [websec-001](../references/Web安全.md#websec-001) |
| 1.00 | 不知道要不要逆签名 |  | [websec-001](../references/Web安全.md#websec-001) |
| 1.00 | 签名可能根本没用 |  | [websec-001](../references/Web安全.md#websec-001) |
| 1.00 | 参数太多不知从哪下手 |  | [websec-002](../references/Web安全.md#websec-002) |
| 1.00 | 看不出哪个字段是校验值 |  | [websec-002](../references/Web安全.md#websec-002) |
| 1.00 | 搜 sign 几百条结果 |  | [websec-003](../references/Web安全.md#websec-003) |
| 1.00 | 定位不到签名代码 |  | [websec-003](../references/Web安全.md#websec-003) |
| 1.00 | 不知道该花多少力气 |  | [websec-004](../references/Web安全.md#websec-004) |
| 1.00 | sign 是否一定要还原 |  | [websec-004](../references/Web安全.md#websec-004) |
| 1.00 | 怕白做整条签名链 |  | [websec-004](../references/Web安全.md#websec-004) |
| 1.00 | 旧包重放报签名错 |  | [websec-005](../references/Web安全.md#websec-005) |
| 1.00 | 改完参数就提示过期 |  | [websec-005](../references/Web安全.md#websec-005) |
| 1.00 |  | `认证过期` | [websec-005](../references/Web安全.md#websec-005) |
| 1.00 |  | `invalid signature` | [websec-005](../references/Web安全.md#websec-005) |
| 1.00 | 改了参数就被拒 |  | [websec-006](../references/Web安全.md#websec-006) |
| 1.00 | 提示客户端身份校验失败 |  | [websec-006](../references/Web安全.md#websec-006) |
| 1.00 |  | `"errno":-105` | [websec-006](../references/Web安全.md#websec-006) |
| 1.00 |  | `客户端身份校验失败` | [websec-006](../references/Web安全.md#websec-006) |
| 1.00 | 改 page 后签名错误 |  | [websec-007](../references/Web安全.md#websec-007) |
| 1.00 | 改一个字段就失败 |  | [websec-007](../references/Web安全.md#websec-007) |
| 1.00 | 原包重放领不到 |  | [websec-008](../references/Web安全.md#websec-008) |
| 1.00 | 重放没反应 |  | [websec-008](../references/Web安全.md#websec-008) |
| 1.00 | 以为没漏洞 |  | [websec-008](../references/Web安全.md#websec-008) |
| 1.00 | 一次成功就写结论 |  | [websec-009](../references/Web安全.md#websec-009) |
| 1.00 | 怀疑无幂等但证明不了 |  | [websec-009](../references/Web安全.md#websec-009) |
| 1.00 |  | `429` | [websec-009](../references/Web安全.md#websec-009) |
| 1.00 |  | `Too Many Requests` | [websec-009](../references/Web安全.md#websec-009) |
| 1.00 | 界面提示失败但接口没报错 |  | [websec-010](../references/Web安全.md#websec-010) |
| 1.00 | 不知道判定在不在本地 |  | [websec-010](../references/Web安全.md#websec-010) |
| 1.00 |  | `isblock` | [websec-010](../references/Web安全.md#websec-010) |
| 1.00 |  | `errorcode` | [websec-010](../references/Web安全.md#websec-010) |
| 1.00 | 改包后无法联网 |  | [websec-012](../references/Web安全.md#websec-012) |
| 1.00 | 重签名功能全消失 |  | [websec-012](../references/Web安全.md#websec-012) |
| 1.00 | 改包后一直网络错误 |  | [websec-012](../references/Web安全.md#websec-012) |
| 1.00 |  | `网络连接失败` | [websec-012](../references/Web安全.md#websec-012) |
| 1.00 |  | `network error` | [websec-012](../references/Web安全.md#websec-012) |
| 1.00 | 模拟器上功能降级 |  | [websec-013](../references/Web安全.md#websec-013) |
| 1.00 | 真机正常模拟器不行 |  | [websec-013](../references/Web安全.md#websec-013) |
| 1.00 |  | `device_register 返回降级标识` | [websec-013](../references/Web安全.md#websec-013) |
| 1.00 | 接口带 UserID 参数 |  | [websec-015](../references/Web安全.md#websec-015) |
| 1.00 | 参数是连号 |  | [websec-015](../references/Web安全.md#websec-015) |
| 1.00 |  | `无权限` | [websec-015](../references/Web安全.md#websec-015) |
| 1.00 | 按钮点不了 |  | [websec-017](../references/Web安全.md#websec-017) |
| 1.00 | 以为没入口就放弃了 |  | [websec-017](../references/Web安全.md#websec-017) |
| 1.00 |  | `401` | [websec-017](../references/Web安全.md#websec-017) |
| 1.00 | 抓到的签名复用被拒 |  | [websec-019](../references/Web安全.md#websec-019) |
| 1.00 | 同样输入结果不同 |  | [websec-019](../references/Web安全.md#websec-019) |
| 1.00 | 存一个值反复用 |  | [websec-019](../references/Web安全.md#websec-019) |
| 1.00 | 签名算出来对不上 |  | [websec-022](../references/Web安全.md#websec-022) |
| 1.00 | 参数一致但 sign 不同 |  | [websec-022](../references/Web安全.md#websec-022) |
| 1.00 | 不知道哪些参数进签名 |  | [websec-023](../references/Web安全.md#websec-023) |
| 1.00 | 签名字段要一个个试 |  | [websec-023](../references/Web安全.md#websec-023) |
| 1.00 | 本地都过了一切仍被拒 |  | [websec-027](../references/Web安全.md#websec-027) |
| 1.00 | 交易还是失败 |  | [websec-027](../references/Web安全.md#websec-027) |
| 1.00 |  | `风控拦截` | [websec-027](../references/Web安全.md#websec-027) |
| 1.00 |  | `交易失败` | [websec-027](../references/Web安全.md#websec-027) |
| 1.00 | 界面显示会员了算不算成功 |  | [websec-028](../references/Web安全.md#websec-028) |
| 1.00 | UI 变了但功能没通 |  | [websec-028](../references/Web安全.md#websec-028) |
| 1.00 |  | `账户不存在` | [websec-028](../references/Web安全.md#websec-028) |
| 1.00 |  | `密码错误` | [websec-028](../references/Web安全.md#websec-028) |
| 1.00 | UI 变了功能没通 |  | [websec-011](../待验证/Web安全.md#websec-011) `孤例` |
| 1.00 | 403 但参数看着没错 |  | [websec-014](../待验证/Web安全.md#websec-014) `孤例` |
| 1.00 | 分享能换时长 |  | [websec-016](../待验证/Web安全.md#websec-016) `孤例` |
| 1.00 | 抓到三段式 token |  | [websec-018](../待验证/Web安全.md#websec-018) `孤例` |
| 1.00 | nonce 看起来是随机 |  | [websec-020](../待验证/Web安全.md#websec-020) `孤例` |
| 1.00 | nonce 要不要复刻生成逻辑 |  | [websec-021](../待验证/Web安全.md#websec-021) `孤例` |
| 1.00 | JS 全混淆找不到入口 |  | [websec-024](../待验证/Web安全.md#websec-024) `孤例` |
| 1.00 | 扣下来的 JS 跑不起来 |  | [websec-025](../待验证/Web安全.md#websec-025) `孤例` |
| 1.00 | 滑块/风控每次结果不同 |  | [websec-026](../待验证/Web安全.md#websec-026) `孤例` |
| 1.00 | 地址栏改参数没反应 |  | [websec-029](../待验证/Web安全.md#websec-029) `孤例` |
| 0.50 |  | `403` | [websec-015](../references/Web安全.md#websec-015) |
| 0.50 |  | `403` | [websec-017](../references/Web安全.md#websec-017) |
| 0.33 |  | `invalid sign` | [websec-019](../references/Web安全.md#websec-019) |
| 0.33 |  | `invalid sign` | [websec-022](../references/Web安全.md#websec-022) |
| 0.33 |  | `invalid sign` | [websec-028](../references/Web安全.md#websec-028) |
| 0.25 |  | `签名错误` | [websec-007](../references/Web安全.md#websec-007) |
| 0.25 |  | `签名错误` | [websec-019](../references/Web安全.md#websec-019) |
| 0.25 |  | `签名错误` | [websec-023](../references/Web安全.md#websec-023) |
