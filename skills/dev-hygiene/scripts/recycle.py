"""删除走 Windows 回收站 —— dev-hygiene 模板，复制到项目 ``tools\\`` 下使用。

不在这里重新实现删除逻辑：转调同目录的 ``Remove-ToRecycleBin.ps1``，
保证"只有一个实现"，也保证以后改规则时不会两处不一致。

用法::

    from tools.recycle import recycle, hard_delete

    deleted = recycle("build/tmp")                      # 进回收站，返回被删路径
    recycle(["a.txt", "b.txt"], whatif=True)            # 只看会删什么
    hard_delete(".venv", reason="项目完事；uv.lock 与 HANDOVER 重建命令已实测")

命令行::

    uv run python tools/recycle.py build/tmp --whatif
    uv run python tools/recycle.py .venv --hard-delete --reason "项目完事，锁文件已实测可重建"

前置：Windows + pwsh 7。``Remove-ToRecycleBin.ps1`` 必须与本文件同目录（项目 ``tools\\``）。

编码注意（本机实测坑）：Windows 上 Python 的 stdout 默认是 cp936，脚本 ``print`` 中文时，
按 UTF-8 读日志的终端会看到乱码 —— 与删除逻辑无关。本模块因此调用 ps1 时带 ``-Quiet``，
只用退出码判断成败、自己构造返回值（不解析 pwsh 的中文输出）。要打印中文的入口脚本，
请在开头加 ``sys.stdout.reconfigure(encoding="utf-8")``，或运行前设 ``$env:PYTHONUTF8='1'``。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Union

__all__ = ["recycle", "hard_delete", "RecycleError"]

PathLike = Union[str, Path]

#: 与唯一实现同目录（项目里就是 tools\Remove-ToRecycleBin.ps1）
PS1 = Path(__file__).with_name("Remove-ToRecycleBin.ps1")


class RecycleError(RuntimeError):
    """删除失败。绝不降级为永久删除，直接把问题抛给调用方。"""


def _run(
    paths: List[PathLike], *, whatif: bool, hard: bool, reason: str | None
) -> List[Path]:
    if not PS1.is_file():
        raise RecycleError(
            f"缺少唯一实现 {PS1}：把 dev-hygiene 的 scripts\\Remove-ToRecycleBin.ps1 "
            "复制到与本文件同目录（通常是项目 tools\\）"
        )

    # 用 `pwsh -Command` 在会话内以 -Path 数组调用：
    # `pwsh -File` 传不进逗号数组（会变成单个字符串 "a,b"），而 PowerShell 又不允许重复 -Path。
    quoted = ",".join("'" + str(p).replace("'", "''") + "'" for p in paths)
    code = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
    code += f"& '{PS1}' -Path @({quoted}) -Quiet"
    if whatif:
        code += " -WhatIf"
    if hard:
        code += " -HardDelete -Reason '" + (reason or "").replace("'", "''") + "'"

    cmd = ["pwsh", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code]
    proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        raise RecycleError(detail)
    return [Path(p) for p in paths]


def recycle(paths: Union[PathLike, Iterable[PathLike]], *, whatif: bool = False) -> List[Path]:
    """把文件/目录移进回收站；返回被处理的路径。失败抛 :class:`RecycleError`。"""
    items = [paths] if isinstance(paths, (str, Path)) else list(paths)
    if not items:
        raise ValueError("没有要删除的路径")
    return _run(items, whatif=whatif, hard=False, reason=None)


def hard_delete(
    paths: Union[PathLike, Iterable[PathLike]], *, reason: str, whatif: bool = False
) -> List[Path]:
    """永久删除 —— 仅用于豁免清单（.venv、uv 缓存、node_modules、%TEMP% 本次临时文件）。

    ``reason`` 必填，写清为什么它属于豁免清单；调用前应已确认 uv.lock 与重建命令可用。
    """
    if not reason or not reason.strip():
        raise ValueError("hard_delete 必须给出 reason（豁免清单依据）")
    items = [paths] if isinstance(paths, (str, Path)) else list(paths)
    if not items:
        raise ValueError("没有要删除的路径")
    return _run(items, whatif=whatif, hard=True, reason=reason)


def _main(argv: List[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:  # 老解释器/被包装过的 stdout
            pass

    whatif = "--whatif" in args
    hard = "--hard-delete" in args
    reason = None
    if "--reason" in args:
        i = args.index("--reason")
        reason = args[i + 1] if i + 1 < len(args) else None
        del args[i : i + 2]
    paths = [a for a in args if not a.startswith("--")]

    if not paths:
        print(__doc__.split("命令行::")[1].split("前置：")[0].strip())
        return 2
    try:
        done = hard_delete(paths, reason=reason or "", whatif=whatif) if hard \
            else recycle(paths, whatif=whatif)
    except (RecycleError, ValueError) as exc:
        print(f"失败：{exc}", file=sys.stderr)
        return 1
    kind = "永久删除" if hard else "移入回收站"
    for p in done:
        print(f"{kind}：{p}" + ("（预演，未真正执行）" if whatif else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
