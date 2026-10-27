"""iv8 环境库加载器 —— 成长型补环境的核心。

设计目标：每逆向一个新站点，只**增量**沉淀差异，而不是重头补环境。

三层结构：
    base.py          基线指纹（Chrome/Windows 桌面），所有站点共用
    polyfills/       缺失 API 补丁（按症状索引，命中的自动加载）
    sites/<name>.yml 站点档案：只写该站**特有**的差异

加载优先级（后者覆盖前者）：
    base  <  polyfill  <  site  <  调用方显式传入
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ENV_DIR = Path(__file__).resolve().parent
POLYFILL_DIR = ENV_DIR / "polyfills"
PATCH_DIR = ENV_DIR / "patches"
SITE_DIR = ENV_DIR / "sites"


# ---------------------------------------------------------------- 深度合并

def deep_merge(base: dict, overlay: dict) -> dict:
    """递归合并字典。overlay 中的标量与列表直接覆盖 base。"""
    out = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------- 极简 YAML

def load_simple_yaml(path: Path) -> dict:
    """读取本站点档案用的极简 YAML（嵌套映射 + 标量，够用即可）。

    不引入 PyYAML 依赖：档案结构固定且简单，手写解析更可控。
    支持：
        key: value
        key:
          nested: value
        # 注释
    值会按 int / float / bool / null / str 自动转型，引号内的保持字符串。
    """
    if not path.exists():
        raise FileNotFoundError(f"站点档案不存在: {path}")

    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        parent = stack[-1][1]

        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()

        if val == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _coerce(val)

    return root


def _coerce(val: str) -> Any:
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    low = val.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none", "~"):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


# ---------------------------------------------------------------- polyfill

def load_manifest() -> dict:
    mf = POLYFILL_DIR / "manifest.json"
    if not mf.exists():
        return {"polyfills": []}
    return json.loads(mf.read_text(encoding="utf-8"))


def select_polyfills(site: str | None = None, tags: list[str] | None = None) -> list[dict]:
    """挑出本次要加载的 polyfill。

    规则：
      - manifest 里 always: true 的一律加载
      - 显式传入的 tags 命中则加载
      - site 命中 sites 列表则加载
    """
    tags = set(tags or [])
    chosen = []
    for item in load_manifest().get("polyfills", []):
        if item.get("always"):
            chosen.append(item)
            continue
        if tags & set(item.get("tags", [])):
            chosen.append(item)
            continue
        if site and site in item.get("sites", []):
            chosen.append(item)
    return chosen


def polyfill_source(item: dict) -> str:
    f = POLYFILL_DIR / item["file"]
    if not f.exists():
        raise FileNotFoundError(f"polyfill 文件缺失: {f}")
    return f.read_text(encoding="utf-8")


# ---------------------------------------------------------------- 主导出

def build_environment(site: str | None = None, overrides: dict | None = None) -> dict:
    """组装完整 environment 字典。"""
    from base import BASE_ENVIRONMENT  # type: ignore  # 同目录导入

    env = json.loads(json.dumps(BASE_ENVIRONMENT))  # 深拷贝

    if site:
        site_file = SITE_DIR / f"{site}.yml"
        profile = load_simple_yaml(site_file)
        env = deep_merge(env, profile.get("environment", {}))

    if overrides:
        env = deep_merge(env, overrides)

    return env


def load_site(site: str) -> dict:
    return load_simple_yaml(SITE_DIR / f"{site}.yml")


def list_sites() -> list[str]:
    if not SITE_DIR.exists():
        return []
    return sorted(p.stem for p in SITE_DIR.glob("*.yml"))


__all__ = [
    "ENV_DIR", "POLYFILL_DIR", "PATCH_DIR", "SITE_DIR",
    "deep_merge", "load_simple_yaml", "load_manifest",
    "select_polyfills", "polyfill_source",
    "build_environment", "load_site", "list_sites",
]
