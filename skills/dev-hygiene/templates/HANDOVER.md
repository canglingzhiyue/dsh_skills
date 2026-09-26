# <项目名> 交接文档（HANDOVER）

> **目的**：换一台机器、换一个 DSH 环境，照着本文档就能从零重建并跑通，不需要问任何人。
> **维护规则**（见 `dev-hygiene` skill）：改本文之前，**先把旧版复制成 `docs\handover-history\HANDOVER-YYYY-MM-DD.md`**，
> 再改本文，并在文末「变更记录」追加一行。有 git 的项目改完提交一次。

## 1. 这是什么（一句话）

<做什么用的、给谁用、解决什么问题>

## 2. 环境

| 项 | 值 |
|---|---|
| OS | Windows <版本> |
| shell | pwsh 7（`pwsh --version` 应输出 7.x） |
| Python | <3.12.x>，由 uv 托管（版本写在 `.python-version`） |
| uv | <0.11.x>（`uv --version`） |
| 依赖源 | 清华 PyPI `https://pypi.tuna.tsinghua.edu.cn/simple`（全局 + 项目内各配一份） |
| 其它 | <git / node / VC++ 运行库 / 代理 …> |

## 3. 从零重建（逐条复制执行）

```powershell
# 1) 拿到代码
git clone <仓库地址> <目录>        # 或从交付包里解压

# 2) 建环境（按 uv.lock 精确重建，走清华源）
cd <目录>
uv sync

# 3) 冒烟
uv run <入口脚本> --help
```

**期望结果**：<写出正常输出长什么样，越具体越好>

> `.venv` 属于可重建产物，可以随时删掉省空间；删了之后重跑 `uv sync` 即可。

## 4. 运行与验证

| 用途 | 命令 | 期望输出 |
|---|---|---|
| 主流程 | `uv run <脚本> <参数>` | <...> |
| 自检 | `uv run <脚本>` | <...> |

## 5. 目录结构

```
<项目>\
    <入口脚本>.py        一句话说明
    pyproject.toml      依赖声明（含清华源配置）
    uv.lock             锁定版本，必须保留
    .python-version     Python 版本
    tools\              工具脚本（recycle.ps1 / recycle.py 等）
    data\               数据
    output\             产物
    debug\              诊断脚本（有证据价值的保留）
    docs\handover-history\   本档历史版本（回退用）
```

## 6. 数据与凭据来源（**只写从哪取，绝不写值**）

| 东西 | 从哪来 | 备注 |
|---|---|---|
| <登录态 / token> | <控制台菜单 / 重新扫码 / 找谁要> | 凭据不入库、不进备份 |

## 7. 已知坑与限制

- <踩过的坑 + 现象 + 解法>

## 8. 回退方式

| 想回退什么 | 怎么做 |
|---|---|
| 代码 | `git log` → `git checkout <commit>` |
| 环境 | 删 `.venv` 后 `uv sync` |
| 本文档 | `docs\handover-history\HANDOVER-<日期>.md` |

## 9. 不确定 / 待办

- [ ] <还没验证的事、需要用户确认的事>

## 变更记录（只追加，不覆盖）

| 日期 | 改了什么 | 为什么 |
|---|---|---|
| YYYY-MM-DD | 初版 | — |
