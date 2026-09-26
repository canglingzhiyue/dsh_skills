# uv + 清华源配置（本机已验证）

规则 3 的落地细节。目标：**每个项目的 Python 环境都在项目内、依赖走清华源、永不碰 anaconda。**

## 一、全局默认源：`%APPDATA%\uv\uv.toml`

本机路径：`C:\Users\y\AppData\Roaming\uv\uv.toml`（2026-09-15 新建）

```toml
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

- 顶层键就是 uv 的全局设置；`[[index]]` 是表数组，`default = true` 让它成为默认索引。
- 旧的 `--index-url` / `UV_INDEX_URL` 已被标记 deprecated，**不要用**；新写法是 `--default-index` / `UV_DEFAULT_INDEX`。
- 想临时换配置（不动全局）：设 `UV_CONFIG_FILE` 指向另一个 toml，或用 `--no-config` 完全忽略配置文件。

## 二、项目内也写一份（为了换机器零配置重现）

`pyproject.toml` 里（注意是 `tool.uv.index`，比全局那份多一层 `tool.uv`）：

```toml
[[tool.uv.index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

或者项目根放一个 `uv.toml`（写法与全局那份相同，`[[index]]`），效果一样。

**为什么要两份**：全局那份只保本机省事；项目那份让 `git clone` 到任何机器后**不用先配环境**就能快速 `uv sync`。

## 三、新项目标准流程

```powershell
uv init <项目名>
Set-Location <项目名>
uv python pin 3.12                  # 版本按项目需要；结果写进 .python-version
# 删掉 uv init 的示例代码（hello.py / main.py 里的示例函数），只留 pyproject.toml
uv add requests                     # 走清华源，写入 pyproject.toml + uv.lock
uv run python -c "import requests; print(requests.__version__)"
```

- 一律 `uv run <脚本>` 跑东西，**不要**手工 `activate`，也不要 `python xxx.py`（那会用错解释器）。
- `uv sync` 是重建环境的唯一标准命令；`uv.lock` 必须提交/保留。

## 四、禁止事项

- 用 `D:\ProgramsDev\anaconda3\python.exe` 或它的 `pip` 装任何包（本机默认 `python` 就指向它，会静默污染 anaconda）。
- `pip install`（全局）、`uv pip install --system`、`uv pip install` 装到非项目环境。
- 在项目里手写 `requirements.txt` 代替 `pyproject.toml` + `uv.lock`（除非上游只发 requirements）。

## 五、本机实测记录（2026-09-15）

配置用一个临时 `uv.toml`（`UV_CONFIG_FILE` 指向，不改全局）验证：

```text
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true

DEBUG Found stale response for: https://pypi.tuna.tsinghua.edu.cn/simple/six/
DEBUG ... https://pypi.tuna.tsinghua.edu.cn/packages/b7/ce/.../six-1.17.0-py2.py3-none-any.whl
Resolved 1 package in 337ms
Would install 1 package
```

结论：

- 配置写法生效，解析与下载都走清华源（URL 里是 `pypi.tuna.tsinghua.edu.cn`）。
- **直连可达、不需要代理**（本机连 GitHub 才需要那个内网代理，清华源不需要）。
- 解析耗时 ~0.3 s。

## 六、托管 Python：`python-preference = "only-managed"`（2026-09-15 起）

本机原先**没有任何 uv 托管的 Python**（`uv python list --only-installed` 只看到 anaconda 的 3.12.7），
于是 `uv run` 建出的 `.venv` 虽然隔离了包安装，但**基础解释器仍是** `D:\ProgramsDev\anaconda3\python.exe`。
为彻底不碰 anaconda，做了两件事：

1. 装托管 CPython：`uv python install 3.12` → `cpython-3.12.13`，落在
   `%APPDATA%\uv\python\cpython-3.12.13-windows-x86_64-none\`（20.9 MiB，直连 5.3 秒完成，**不需要代理**）；
2. 全局 `uv.toml` 加 `python-preference = "only-managed"`，之后 uv 只用托管解释器。

**TOML 顺序坑（踩过）**：`python-preference` 是顶层键，**必须写在 `[[index]]` 之前**；
写在表数组后面会被归进 `[[index]]` 元素里，静默失效。当前正确的全局文件是：

```toml
python-preference = "only-managed"

[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

验证：新项目里 `uv run python -c "import sys; print(sys.executable)"` 指向项目 `.venv`，
且 uv 的 stderr 显示 `Using CPython 3.12.13`（托管版），**不再出现 anaconda 的 3.12.7**。

**新环境重建**：先 `uv python install <版本>` 再 `uv sync`。若某台机器下不动 GitHub release
（本机 release 直连可达；只有 `git clone github.com` 才需要那个内网代理），就临时把那行改成
`python-preference = "managed"` 或删掉，并在该项目 `HANDOVER.md` 里写明原因。

## 七、暂不设置的东西

`uv python install` 下载 CPython 时走的是 GitHub release（python-build-standalone），对应的镜像变量是
`UV_PYTHON_INSTALL_MIRROR` / `--mirror`。**本机没有核实清华是否镜像该内容，因此不设**，保持默认；
哪天 `uv python install` 慢到无法忍受，再去找可用镜像（清华 TUNA 的 `github-release` 目录或其它镜像站）并补进本节。
