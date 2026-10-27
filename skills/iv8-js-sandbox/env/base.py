"""基线指纹 —— 所有站点共用的 Chrome / Windows 桌面环境。

原则（重要）：
    **能不改就不改。** iv8 内置的默认指纹在原生一致性上是对的
    （描述符 getter 的 toString 就是 [native code]，Symbol.toStringTag 正确）。
    手工覆盖越多，暴露的不一致面越大 —— 补环境最常见的翻车方式就是
    "为了对齐一个字段，改出三个新的矛盾"。

    所以这里**只放跨站点确实需要统一的东西**，站点特有的差异一律写进
    env/sites/<name>.yml，不要往这里堆。

维护规则：
    某个字段被 3 个以上站点档案重复覆盖时，才提升到这里并记一行 HISTORY.md。
"""

from __future__ import annotations

# 基线：一台常见的 Windows 桌面 Chrome。字段取 Chrome 稳定版的典型值，
# 与 iv8 内置默认保持一致的部分**刻意不重复写**，避免固化版本号。
BASE_ENVIRONMENT: dict = {
    "navigator": {
        # 版本号故意留空由站点档案决定：不同站的 JS 会对版本做特性分支，
        # 基线不该替站点做这个决定。
        "platform": "Win32",
        "language": "zh-CN",
        "languages": ["zh-CN", "zh", "en-US", "en"],
        "hardwareConcurrency": 8,
        "deviceMemory": 8,
        "webdriver": False,
    },
    "screen": {
        "width": 1920,
        "height": 1080,
        "availWidth": 1920,
        "availHeight": 1040,
        "colorDepth": 24,
        "pixelDepth": 24,
    },
    "window": {
        "innerWidth": 1920,
        "innerHeight": 947,
        "outerWidth": 1920,
        "outerHeight": 1040,
        "devicePixelRatio": 1.0,
    },
}

# 跨站点通用、但**不通过 environment 注入**的 JS 侧补丁。
# 这些是行为层面的补丁，写在 patches/ 下由 runtime 按需注入。
DEFAULT_PATCHES: list[str] = []
