"""蒸馏工程公共层：路径常量、17 主题映射、笔记头解析、tid 索引缓存、文本归一化。

用途：
    merge_pools / build_anchors / build_symptom_index 三个脚本共用这一层，
    避免每个脚本各写一份"主题怎么映射""笔记头怎么解析"。

用法（可复制运行）：
    import common
    idx = common.build_tid_index()          # 首次扫描 6484 个笔记头并缓存，之后直接读缓存
    print(idx['632562']['year'], idx['632562']['platform'])
    print(common.map_topics(['脱壳加固', '综合实战']))   # -> ['脱壳加固', '综合实战']

关键结论 / 限制：
    - 两库笔记 schema 同构（8 节 + 头元数据），唯一差异是 kanxue 多「方向」字段（实测 86% 覆盖）。
    - 52pojie 的 `experience_pool.json` 把经验点**平铺**挂在"笔记×主题"记录下，
      同一篇笔记会在多个主题键里重复出现 —— 必须按 tid 去重，否则篇数虚高。
    - 主题映射**先精确匹配 17 个正题，再按关键词兜底**；兜底规则有顺序，改顺序会改归类。
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

# ==== 路径常量（本机实测，2026-11-01）====
CASE_ROOT = Path(r"D:\AI_python\reverse-cases\2026-11-01_skills-distill")
LIB_52PJ = Path(r"D:\AI_python\reverse\52pojie")
LIB_KX = Path(r"D:\AI_python\reverse\kanxue")

NOTES_52PJ = LIB_52PJ / "notes"
NOTES_KX = LIB_KX / "notes"
POOL_52PJ = LIB_52PJ / "data" / "experience_pool.json"
POOL_KX = LIB_KX / "data" / "experience_pool.json"

DATA_DIR = CASE_ROOT / "data"
ANCHOR_DIR = DATA_DIR / "anchors"
CLUSTER_DIR = DATA_DIR / "clusters"
OUT_DIR = CASE_ROOT / "output"

TID_INDEX_CACHE = DATA_DIR / "tid_index.json"

# ==== 平台标识 ====
P_52PJ = "52pj"
P_KX = "kanxue"

# ==== 17 个正题（12+11 份手册取并集 = 15，加两个笔记级主题）====
CANON_THEMES = [
    "脱壳加固", "Hook调试", "静态分析", "协议抓包", "算法还原", "改包会员",
    "环境工具", "AI辅助", "综合实战", "JS逆向", "Windows逆向", "VMP还原",
    "Web安全", "系统内核", "小程序", "样本分析", "游戏逆向",
]

# 兜底关键词规则：**顺序敏感**。算法还原必须先于改包会员判定，
# 否则「注册机/算法」类笔记会被「破解」这个词抢走（实测 52pojie 标签里两者大量共现）。
_FALLBACK_RULES = [
    ("脱壳加固", ("脱壳", "加固", "壳中", "壳.")),
    ("VMP还原", ("vmp", "vmprotect", "虚拟机保护")),
    ("Hook调试", ("hook", "xposed", "frida", "注入", "插桩", "桩")),
    ("算法还原", ("算法", "注册机", "keygen", "加密算法", "序列号", "码表", "校验")),
    ("协议抓包", ("协议", "抓包", "封包", "sign", "签名")),
    ("小程序", ("小程序", "miniapp", "wxapkg", "wmpf")),
    ("系统内核", ("内核", "驱动", "提权", "kernel", "ebpf", "selinux")),
    ("样本分析", ("样本", "病毒", "恶意", "勒索", "木马", "应急", "后门", "挖矿")),
    ("游戏逆向", ("游戏", "外挂", "辅助", "unity", "il2cpp", "cocos", "lua")),
    ("改包会员", ("改包", "会员", "vip", "去广告", "破解", "爆破", "内购", "支付")),
    ("JS逆向", ("js逆向", "jsvmp", "jsvmp", "补环境", "webpack", "ast", "混淆")),
    ("Web安全", ("web安全", "漏洞", "渗透", "攻击链", "sql", "xss", "ssrf")),
    ("Windows逆向", ("windows", "vb", "delphi", ".net", "pe文件", "win32", "crackme", "od")),
    ("环境工具", ("环境", "工具", "配置", "安装", "报错", "兼容", "adb", "simulator", "模拟器")),
    ("AI辅助", ("ai辅助", "ai 辅助", "大模型", "gpt", "llm", "claude")),
    ("静态分析", ("静态", "反编译", "jadx", "ida", "jeb", "smali", "dex", "class")),
    ("综合实战", ("综合", "实战")),
]


def map_topics(raw_topics):
    """把原始主题标签映射到 17 个正题。

    参数：
        raw_topics —— 原始标签列表（可能含长尾脏标签，如 "Hook调试、环境工具"、"其他（PWN"）
    返回：
        去重且保序的正题列表；一个都映射不上时返回 ["综合实战"]
    """
    out = []
    for raw in raw_topics or []:
        t = (raw or "").strip()
        if not t:
            continue
        # 1. 精确匹配正题
        hit = None
        for name in CANON_THEMES:
            if t == name:
                hit = name
                break
        # 2. 兜底关键词
        if hit is None:
            low = t.lower()
            for name, kws in _FALLBACK_RULES:
                if any(k in low for k in kws):
                    hit = name
                    break
        # 3. 复合标签拆开再试一次（"Hook调试、环境工具"）
        if hit is None and ("、" in t or "," in t):
            for part in re.split(r"[、,，]", t):
                if part.strip() in CANON_THEMES:
                    hit = part.strip()
                    break
        if hit and hit not in out:
            out.append(hit)
    return out or ["综合实战"]


# ==== 笔记头解析 ====

_RE_URL = re.compile(r"原帖[：:]\s*(\S+)")
_RE_DATE = re.compile(r"发布[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})")
_RE_AUTHOR = re.compile(r"作者[：:]\s*([^｜|\n]+)")
_RE_BOARD = re.compile(r"版块[：:]\s*([^｜|\n]+)")
_RE_TOPICS = re.compile(r"主题[：:]\s*([^｜|\n]+)")
_RE_DIFF = re.compile(r"难度[：:]\s*([^｜|\n]+)")
_RE_DIR = re.compile(r"方向[：:]\s*([^｜|\n]+)")
_RE_H1 = re.compile(r"^#\s+(.+)$", re.M)


def read_note_meta(path: Path, platform: str):
    """读一篇笔记的头元数据。

    参数：
        path     —— 笔记 md 路径
        platform —— common.P_52PJ 或 common.P_KX
    返回：
        dict（tid/title/url/year/author/board/topics_raw/topics/difficulty/direction/file/platform）；
        读不到标题返回 None。
    异常：
        不抛；文件读失败返回 None。
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    head = "\n".join(text.splitlines()[:14])
    m = _RE_H1.search(text[:400])
    title = m.group(1).strip() if m else None
    if not title:
        return None
    year = None
    dm = _RE_DATE.search(head)
    if dm:
        year = int(dm.group(1))
    topics_raw = []
    tm = _RE_TOPICS.search(head)
    if tm:
        topics_raw = [p.strip() for p in re.split(r"[,，、]", tm.group(1)) if p.strip()]
    um = _RE_URL.search(head)
    am = _RE_AUTHOR.search(head)
    bm = _RE_BOARD.search(head)
    fm = _RE_DIFF.search(head)
    dm2 = _RE_DIR.search(head)
    return {
        "tid": path.stem.split("-")[0].split("_")[0],
        "title": title,
        "url": um.group(1) if um else "",
        "year": year,
        "author": am.group(1).strip() if am else "",
        "board": bm.group(1).strip() if bm else "",
        "topics_raw": topics_raw,
        "topics": map_topics(topics_raw),
        "difficulty": fm.group(1).strip() if fm else "",
        "direction": dm2.group(1).strip() if dm2 else "",
        "file": path.name,
        "platform": platform,
    }


def build_tid_index(force=False):
    """扫描两库全部笔记头，产出 tid → 元数据 的索引（带缓存）。

    参数：
        force —— True 时忽略缓存重新扫描（约 6500 个文件，十几秒）
    返回：
        dict[tid] = meta（同 read_note_meta 的字段）
    """
    if TID_INDEX_CACHE.exists() and not force:
        return json.loads(TID_INDEX_CACHE.read_text(encoding="utf-8"))

    print("[蒸馏] 首次构建 tid 索引（扫描两库笔记头）…")
    idx = {}
    for notes_dir, platform in ((NOTES_52PJ, P_52PJ), (NOTES_KX, P_KX)):
        n = 0
        for p in sorted(notes_dir.glob("*.md")):
            if p.name == "INDEX.md":
                continue
            meta = read_note_meta(p, platform)
            if not meta:
                continue
            tid = meta["tid"]
            if tid not in idx:          # 同 tid 两库不重复；52pojie 有 22 个历史重复文件，取先到的
                idx[tid] = meta
                n += 1
        print(f"[蒸馏]   {platform}: 收入 {n:,} 篇")
    TID_INDEX_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TID_INDEX_CACHE.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[蒸馏] tid 索引已缓存 → {TID_INDEX_CACHE}（{len(idx):,} 条）")
    return idx


# ==== 文本处理 ====

_PUNCT = re.compile(r"[\s\*_`#>|｜\-—…·。，、；：！？,.;:!?\"'“”‘’()（）\[\]【】{}<>《》/\\+~^$%&=]+")


def normalize(text: str) -> str:
    """归一化：全角转半角、去标点空白、小写。用于聚类比对，不用于展示。"""
    t = unicodedata.normalize("NFKC", text or "")
    t = _PUNCT.sub("", t)
    return t.lower()


def ngrams(norm_text: str, n=3):
    """把归一化后的文本切成字符 n-gram 集合。

    参数：
        norm_text —— normalize() 的输出
        n         —— gram 长度，默认 3（中文无分词依赖，字符三元组最稳）
    返回：
        frozenset[str]；文本过短时退化为整串一个 gram
    """
    if len(norm_text) <= n:
        return frozenset([norm_text]) if norm_text else frozenset()
    return frozenset(norm_text[i:i + n] for i in range(len(norm_text) - n + 1))
