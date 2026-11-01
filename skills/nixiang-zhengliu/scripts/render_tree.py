"""render_tree.py —— 把规则草案渲染成技能树文件（references / 锚点表 / 症状索引 / 根 SKILL.md）。

输入：`output/drafts/*.evidence.json`（build_evidence_index.py 的产物；缺失时退回 `*.rules.json`）
输出（暂存区，落盘前的一切都在这里）：
    output/nixiang-shu/
      SKILL.md                    根（≤6000 字符，加载协议 + 主题路由表）
      references/<主题>.md         每主题一节（≤12000 字符），按阶段分组，每条规则一个 #### 锚点
      症状索引.md                  短语列 + 报错原文列 → references/<主题>.md#<rule-id>
      锚点/<主题>.tsv              平台｜tid｜年份｜难度｜证据上限｜URL（可回查，无正文）
      已失效.md                    退役规则墓碑（初始为空壳）

用法（可复制运行）：
    cd D:\\AI_python\\reverse-cases\\2026-11-01_skills-distill
    $env:UV_CACHE_DIR = "<本案>\\debug\\uv-cache"; $env:PYTHONIOENCODING='utf-8'
    uv run --no-project python scripts\\render_tree.py

关键结论 / 限制：
    - **只渲染，不创作**：内容全部来自草案；本脚本不做任何"顺手补一句"。
    - 单条规则渲染后超过 RULE_MAX 会被截断 `action` 并记 WARN（宁可截断也不让闸门失守）。
    - references 文件名用中文（实测本机 grep/glob/pwsh 处理中文文件名正常），技能目录名才必须 ASCII。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import common

TREE = common.OUT_DIR / "nixiang-shu"
RULE_MAX = 900
THEME_MAX = 12_000            # 单主题文件字符上限（超了按阶段拆，见 render_theme_split）
STAGE_ORDER = ["侦察", "定位", "校验", "补丁", "验证"]

REQUIRED = ("id", "title", "domain", "stage", "symptom", "judge", "action", "if_not",
            "invalidate_when", "keys", "anchors", "evidence_hint", "img_dependent")


def load_docs():
    """读全部证据化草案；没有 .evidence.json 时退回 .rules.json。"""
    drafts = common.OUT_DIR / "drafts"
    # ★ 修（2026-11-01）：原来"只要存在任一 .evidence.json 就只用它们"，
    #   导致刚提炼完、还没跑证据计数的新主题被整个跳过（实测：三主题只渲染出一个）。
    #   现在逐主题合并：有证据化文件就用它，没有就直接用 rules（等级取 evidence_hint）。
    ev_map = {p.name.replace(".evidence.json", ""): p
              for p in drafts.glob("*.evidence.json")}
    out = []
    for ru in sorted(drafts.glob("*.rules.json")):
        stem = ru.name.replace(".rules.json", "")
        src = ev_map.get(stem, ru)
        out.append((src, json.loads(src.read_text(encoding="utf-8"))))
    return out


def ev_line(rule):
    """渲染一条规则的证据行（精简版）。

    ★ 2026-11-01 瘦身：原写法 `**证据**：strong ｜ 独立来源 5（52pj5） ｜ 年份 2021–2025 ｜ 检索命中 4`
      每条约 62 字符；预算紧到要按字符抠，改为 `证据：strong ｜ 5源(52pj5) ｜ 2021–2025 ｜ 命中4`
      约 40 字符，信息不丢，35 条能省约 800 字符。
    """
    ev = rule.get("evidence") or {}
    level = ev.get("level") or rule.get("evidence_hint") or "未定"
    by = ev.get("by_platform") or {}
    plat = "/".join(f"{k}{v}" for k, v in sorted(by.items())) or "—"
    yrs = f"{ev.get('year_min')}–{ev.get('year_max')}" if ev.get("year_min") else "—"
    cap = "＋缺口" if ev.get("capped_by_gap") else ""
    n = ev.get("n_tids", "—")
    hits = ev.get("n_hits", "—")
    return f"证据：{level}{cap} ｜ {n}源({plat}) ｜ {yrs} ｜ 命中{hits}"


def _rule_lines(rule):
    """把一条规则渲染成行列表（不含截断逻辑）。

    ★ 2026-11-01 评审修复：原来只在标题里写 `#### tuoke-001 标题`，而 Markdown 自动锚点是
      `#tuoke-001-标题`，链接写 `#tuoke-001` **在真实渲染里根本跳不过去**（闸门却因为自己定的
      宽松语义永远 PASS）。现在显式插入 `<a id="tuoke-001"></a>`，链接才真正可达。

    ★ 同轮瘦身：字段标签去掉加粗与多余空行（每条省约 20 字符），给内容留预算。
    """
    rid = rule.get("id", "?")
    anchors = ",".join(str(t) for t in (rule.get("anchors") or [])[:8])
    symptom = "；".join(rule.get("symptom") or [])
    errs = "；".join(f"`{e}`" for e in (rule.get("error_patterns") or []))
    return [
        f'<a id="{rid}"></a>',
        f"#### {rid} {rule.get('title','')}",
        f"- 症状：{symptom}" + (f"　报错：{errs}" if errs else ""),
        f"- 判断：{rule.get('judge','')}",
        f"- 动作：{rule.get('action','')}",
        f"- 无效则：{rule.get('if_not','无（无已知替代路径）')}",
        f"- 失效条件：{rule.get('invalidate_when','')}",
        f"- {ev_line(rule)}",
        f"- 锚点：{anchors}" + ("　依据在图中，未复核" if rule.get("img_dependent") else ""),
        "",
    ]


def render_rule(rule):
    """渲染单条规则为 markdown 段（≤RULE_MAX 字符）。"""
    miss = [k for k in REQUIRED if rule.get(k) in (None, "", [])]
    warns = [f"缺字段 {','.join(miss)}"] if miss else []
    text = "\n".join(_rule_lines(rule))
    if len(text) > RULE_MAX:
        # 截断动作描述，保留判断链与失效条件（这两项是不许丢的）
        over = len(text) - RULE_MAX
        action = str(rule.get("action") or "")
        keep = max(40, len(action) - over - 20)
        truncated = dict(rule)
        truncated["action"] = action[:keep] + "…（截断，详见锚点原帖）"
        warns.append(f"超 {RULE_MAX} 字符已截断 action")
        text = "\n".join(_rule_lines(truncated))
    return text, warns


def render_theme(doc, title_suffix="", compact=False):
    """渲染一个主题文件。

    参数：
        doc          —— 主题草案（含 theme / rules）
        title_suffix —— 追加到 H1 的后缀，如「· 侦察」。按阶段拆分后每个文件
                        只含一个阶段，标题不标阶段会让人以为是整个主题（实测踩过）。
    返回：
        (markdown, 规则数, WARN 列表)
    """
    theme = doc.get("theme", "未命名")
    rules = doc.get("rules") or []
    by_stage = defaultdict(list)
    for r in rules:
        by_stage[r.get("stage") or "定位"].append(r)
    # ★ 2026-11-01 修：拆分后每个子文件都重付一次页头，6 份就是 1,131 字符的凭空开销
    #   （实测：某主题整篇 12,037 只超 37 字符，一拆反而涨到 13,168）。compact=True 时只留一行。
    if compact:
        lines = [f"# {theme}{title_suffix}", f"> 规则 {len(rules)} 条；用法见上级主题页。", ""]
    else:
        lines = [
            f"# {theme}{title_suffix}",
            "",
            f"> 由 `nixiang-shu` 蒸馏生成 ｜ 规则 {len(rules)} 条"
            f" ｜ 来源：52pojie 12 份手册 + 看雪 11 份手册（合并去重）",
            "> 用法：按**症状**从上往下扫，命中就照 `判断 → 动作` 走；走不通看 `无效则`。",
            "> 锚点是 tid：语料库在本地时可 `grep -r <tid> D:\\AI_python\\reverse\\*\\notes\\` 回查原文。",
            "",
        ]
    warns = []
    for stage in STAGE_ORDER + sorted(set(by_stage) - set(STAGE_ORDER)):
        group = by_stage.get(stage)
        if not group:
            continue
        lines += [f"## 阶段：{stage}", ""]
        for r in sorted(group, key=lambda x: str(x.get("id"))):
            text, w = render_rule(r)
            lines.append(text)
            for x in w:
                warns.append(f"{r.get('id')}: {x}")
    return "\n".join(lines), len(rules), warns


def render_anchors(doc, img_index, tid_index):
    """渲染锚点 TSV：平台｜tid｜年份｜难度｜证据上限｜URL（不含任何技术细节）。"""
    rows = ["# 平台\ttid\t年份\t难度\t证据上限\tURL"]
    seen = set()
    for r in doc.get("rules") or []:
        for t in r.get("anchors") or []:
            t = str(t)
            if t in seen:
                continue
            seen.add(t)
            meta = tid_index.get(t) or {}
            cap = (img_index.get(t) or {}).get("evidence_cap", "—")
            plat = meta.get("platform", "—")
            rows.append(f"{plat}\t{t}\t{meta.get('year','—')}\t{meta.get('difficulty','—')}\t{cap}\t{meta.get('url','')}")
    return "\n".join(rows) + "\n"


def _phrase_weight_map(docs, staging_rows):
    """统计每个症状短语的"稀缺度权重"（评审 Q2 的 C 方案）。

    口径（**脚本推导，禁人工填**）：
        df = 该短语（归一化后）在多少条规则里出现过（含孤例指针行）
        权重 = 1 / df —— 只有一条规则用到 = 1.0（最强定位力），多条共用 = 更低

    为什么要有这一列（评审实测依据）：完全重复短语 0 条，但**二义**真实存在
    （`newPosition > limit` 同时指向 jingtai-013 与 028）——只有排序能把歧义显式化。

    返回：
        dict{normalized_phrase: weight}
    """
    from collections import Counter
    df = Counter()
    for doc in docs:
        for r in doc.get("rules") or []:
            for s in (r.get("symptom") or [])[:3]:
                df[common.normalize(s)] += 1
            for e in (r.get("error_patterns") or [])[:3]:
                df[common.normalize(e)] += 1
    for row in staging_rows:
        for s in row.get("symptom") or []:
            df[common.normalize(s)] += 1
    return {k: round(1.0 / v, 2) for k, v in df.items() if k}


def render_symptom_index(docs, mapping, staging_rows=None):
    """渲染**按主题拆分**的症状索引：权重列 + 短语 + 报错原文 → <规则所在文件>#<rule-id>。

    ★ 2026-11-01 评审修复：原来出全局单份索引。按 17 主题外推，全局索引会到 100 KB 量级，
      而单份索引预算 8,000 字符——算术上不可能（评审盲区 #1）。改为每主题一份。

    ★ 同轮采纳评审 Q2=C 与 Q4=C：
      · 加**权重列**（1/df，脚本推导）——把"同一报错指向多条规则"的二义显式化，
        权重 1.0 = 该短语只指向一条规则，定位力最强；
      · **孤例也进索引**（标注 `孤例`），否则 `tuoke-017` 那种现役壳最典型报错 AI 完全看不到。

    返回：
        (files, rows) —— files 是 {相对路径: 文本}；rows 是总行数
    """
    staging_rows = staging_rows or []
    weights = _phrase_weight_map(docs, staging_rows)
    files = {}
    total_rows = 0
    for doc in docs:
        theme = doc.get("theme", "")
        lines = [
            f"# 症状索引 · {theme}",
            "",
            "> 命中任一列即可跳转。短语列是「用户会怎么说」，报错原文列可直接搜。",
            "> **权重** = 1/df（脚本推导）：1.0 表示该短语只指向一条规则、定位力最强；"
            "越低说明多条规则共用，需结合上下文判。",
            "> 标 `孤例` 的行只有单一来源，**只作定位线索、不可直接采信**。",
            "",
            "| 权重 | 症状（短语） | 报错原文 | 去哪 |",
            "|---|---|---|---|",
        ]
        rows = []
        for r in doc.get("rules") or []:
            path = mapping.get(str(r.get("id")))
            if not path:
                continue
            target = f"../{path.as_posix()}#{r.get('id')}"
            for s in (r.get("symptom") or [])[:3]:
                rows.append((weights.get(common.normalize(s), 1.0), s, "", r.get("id"), target, ""))
            for e in (r.get("error_patterns") or [])[:3]:
                rows.append((weights.get(common.normalize(e), 1.0), "", f"`{e}`", r.get("id"), target, ""))
        for row in staging_rows:
            if row.get("theme") != theme:
                continue
            for s in (row.get("symptom") or [])[:1]:
                rows.append((weights.get(common.normalize(s), 1.0), s, "", row.get("id"),
                             f"../{row['path'].as_posix()}#{row.get('id')}", "孤例"))
        if not rows:
            continue
        rows.sort(key=lambda x: -x[0])
        for w, s, e, rid, target, tag in rows:
            label = f"[{rid}]({target})" + (f" `{tag}`" if tag else "")
            lines.append(f"| {w:.2f} | {s} | {e} | {label} |")
        files[Path("症状索引") / f"{theme}.md"] = "\n".join(lines) + "\n"
        total_rows += len(rows)
    return files, total_rows


def render_root(docs):
    """渲染根 SKILL.md（加载协议 + 主题路由表）。"""
    lines = [
        "---",
        "name: nixiang-shu",
        "description: 逆向树 —— 两库（52pojie 4999 篇 + 看雪 1485 篇）经验蒸馏成的判断链技能树。"
        "按症状查：脱壳闪退、重打包白屏、Hook 不生效、签名参数定位、加固版本判别、反调试对抗等。"
        "触发：卡住了、没思路、报错、闪退、装不上、脱壳、改包、Hook、签名、反调试、算法还原。",
        "---",
        "",
        "# nixiang-shu —— 逆向树",
        "",
        "**这不是操作手册，是判断链。** 每条规则都是「看到什么 → 凭什么推断 → 所以做什么 → 不通换哪条」。",
        "",
        "## 加载协议（照做，不要一次读完）",
        "",
        "1. **先看症状索引** `症状索引.md`：拿你手上的现象（用户口吻）或报错原文去搜，命中即跳转。",
        "2. **只读命中的那一个主题文件**：`references/<主题>.md`，读该规则的四行就够。",
        "3. **锚点回查**：规则末尾的 tid 可回本地语料库查原文；跨机器时用 `锚点/<主题>.tsv` 里的 URL。",
        "4. **走不通**：先看该规则的 `失效条件`，再看 `已失效.md`（墓碑），最后才考虑新开一条规则。",
        "5. **本机工具事实**以 `$DSH_HOME\\reverse\\capabilities.md` 为准，不要相信笔记里写的工具版本。",
        "",
        "## 主题路由表",
        "",
        "| 主题 | 规则数 | 主题页 | 症状索引 |",
        "|---|---|---|---|",
    ]
    for doc in docs:
        theme = doc.get("theme", "")
        n = len(doc.get("rules") or [])
        lines.append(f"| {theme} | {n} | [references/{theme}.md](references/{theme}.md) "
                     f"| [症状索引/{theme}.md](症状索引/{theme}.md) |")
    lines += [
        "",
        "## 预算（由 `check_budget.py` 卡）",
        "",
        "根 ≤6,000 字符 ｜ 单文件 ≤12,000 ｜ **主题合计 ≤11,000** ｜ 索引单份 ≤8,000、合计 ≤60,000 "
        "｜ 全树 ≤200,000 字符 ｜ 单次加载 ≤30,000 字符。",
        "拆文件不降低主题合计——超了必须**砍规则或压措辞**，不许靠「反正按需加载」糊过去。",
        "",
    ]
    return "\n".join(lines)


def split_rules(doc):
    """把规则分成「进主树」与「进暂存区」两拨。

    口径（plan.md §五）：**孤例（证据等级 single）只能进暂存区，进不了主树**；
    它要升级得有旁证或第二来源，不是靠人觉得"这条挺好"。

    返回：
        (main_rules, staging_rules, doc_main, doc_staging)
    """
    main, staging = [], []
    for r in doc.get("rules") or []:
        level = (r.get("evidence") or {}).get("level") or r.get("evidence_hint")
        (main if level in ("strong", "weak") else staging).append(r)
    doc_main = dict(doc)
    doc_main["rules"] = main
    doc_staging = dict(doc)
    doc_staging["rules"] = staging
    return main, staging, doc_main, doc_staging


def render_staging(doc):
    """渲染暂存区文件（孤例待实测）。"""
    theme = doc.get("theme", "未命名")
    rules = doc.get("rules") or []
    lines = [
        f"# {theme} · 待验证（孤例）",
        "",
        f"> **不进主树**：这 {len(rules)} 条只有 1 个独立来源，按口径只能待在暂存区。",
        "> 升级条件：第二个独立来源出现，或本机实测通过（实测记录写进行尾的「实测记录」）。",
        "",
    ]
    for r in sorted(rules, key=lambda x: str(x.get("id"))):
        text, _w = render_rule(r)
        lines.append(text)
        lines.append("- **实测记录**：（未实测）")
        lines.append("")
    return "\n".join(lines)


def render_theme_split(doc, theme_max):
    """渲染主题；单文件超预算时**按阶段拆成子目录**，另生成一个薄索引页。

    为什么拆阶段而不是砍内容（plan.md §四 双轴矩阵：域为目录、阶段为节）：
        16,253 字符的「脱壳加固」砍到 12,000 必须删掉 1/4 的判断链，
        那是把最贵的部分扔掉；按阶段拆开后每个文件 3–5 KB，命中时只读一节。

    返回：
        (files, warns, mapping) —— files 是 {相对路径: 文本}；mapping 是 {rule_id: 相对路径}，
        供症状索引把链接指向**规则真正所在的那个文件**（拆分后不再是主题根文件）。
    """
    md, n, warns = render_theme(doc)
    theme = doc.get("theme", "未命名")
    if len(md) <= theme_max:
        rel = Path("references") / f"{theme}.md"
        mapping = {str(r.get("id")): rel for r in doc.get("rules") or []}
        return {rel: md}, warns, mapping
    by_stage = defaultdict(list)
    for r in doc.get("rules") or []:
        by_stage[r.get("stage") or "定位"].append(r)
    files = {}
    mapping = {}
    idx = [
        f"# {theme}（分阶段索引）",
        "",
        f"> 该主题共 {n} 条规则，因单文件超 {theme_max:,} 字符预算，按阶段拆分。",
        "> 用法：先看 `症状索引.md` 定位到 `文件#锚点`，只读那一节，不要整目录通读。",
        "",
        "| 阶段 | 条数 | 文件 |",
        "|---|---|---|",
    ]
    for stage in STAGE_ORDER + sorted(set(by_stage) - set(STAGE_ORDER)):
        group = by_stage.get(stage)
        if not group:
            continue
        sub = dict(doc)
        sub["rules"] = group
        text, _n2, w2 = render_theme(sub, title_suffix=f" · {stage}", compact=True)
        rel = Path("references") / theme / f"{stage}.md"
        files[rel] = text
        warns += w2
        for r in group:
            mapping[str(r.get("id"))] = rel
        # ★ 相对链接要按**索引页所在目录**（references/）算，不能按树根算。
        #   写成 references/<主题>/<阶段>.md 会指向 references/references/...（实测踩过）。
        idx.append(f"| {stage} | {len(group)} | [{theme}/{stage}.md]({theme}/{stage}.md) |")
    files[Path("references") / f"{theme}.md"] = "\n".join(idx) + "\n"
    return files, warns, mapping


def run():
    """主流程：读草案 → 渲染各类文件 → 写盘。"""
    docs = load_docs()
    if not docs:
        print("[渲染] 没有可渲染的草案")
        return None
    img_index = json.loads((common.DATA_DIR / "img_index.json").read_text(encoding="utf-8")) \
        if (common.DATA_DIR / "img_index.json").exists() else {}
    tid_index = common.build_tid_index()

    # ★ 不做删除动作（dev-hygiene 红线：删除一律走回收站，不用 unlink/rmdir）。
    #   原地覆盖写；覆盖不到的旧文件只报 WARN，交人工决定。
    before = {p.relative_to(TREE) for p in TREE.rglob("*") if p.is_file()} if TREE.exists() else set()
    (TREE / "references").mkdir(parents=True, exist_ok=True)
    (TREE / "锚点").mkdir(parents=True, exist_ok=True)

    written = set()
    all_warns = []
    main_docs = []
    staging_count = 0
    staging_rows = []
    rule_path = {}
    for _p, doc in docs:
        theme = doc.get("theme", "未命名")
        main_rules, staging_rules, doc_main, doc_staging = split_rules(doc)
        main_docs.append(doc_main)
        for r in staging_rules:                 # 孤例指针行：进症状索引但不进主树
            staging_rows.append({
                "theme": theme,
                "id": r.get("id"),
                "path": Path("待验证") / f"{theme}.md",
                "symptom": r.get("symptom") or [],
            })
        files, warns, mapping = render_theme_split(doc_main, THEME_MAX)
        rule_path.update(mapping)
        for rel, text in files.items():
            (TREE / rel).parent.mkdir(parents=True, exist_ok=True)
            (TREE / rel).write_text(text, encoding="utf-8")
            written.add(rel)
        rel2 = Path("锚点") / f"{theme}.tsv"
        (TREE / rel2).write_text(render_anchors(doc_main, img_index, tid_index), encoding="utf-8")
        written.add(rel2)
        all_warns += warns
        if staging_rules:
            rel3 = Path("待验证") / f"{theme}.md"
            (TREE / rel3).parent.mkdir(parents=True, exist_ok=True)
            (TREE / rel3).write_text(render_staging(doc_staging), encoding="utf-8")
            written.add(rel3)
            staging_count += len(staging_rules)
        total_chars = sum(len(t) for t in files.values())
        print(f"[渲染] {theme}：主树 {len(main_rules)} 条（{total_chars:,} 字符 / {len(files)} 个文件）"
              f"｜暂存区 {len(staging_rules)} 条")

    idx_files, n_rows = render_symptom_index(main_docs, rule_path, staging_rows)
    for rel, text in idx_files.items():
        (TREE / rel).parent.mkdir(parents=True, exist_ok=True)
        (TREE / rel).write_text(text, encoding="utf-8")
        written.add(rel)
    idx_chars = sum(len(t) for t in idx_files.values())
    print(f"[渲染] 症状索引：{len(idx_files)} 份 / {n_rows} 行 / {idx_chars:,} 字符（只收主树规则）")

    root = render_root(main_docs)
    (TREE / "SKILL.md").write_text(root, encoding="utf-8")
    written.add(Path("SKILL.md"))
    print(f"[渲染] 根 SKILL.md：{len(root):,} 字符｜暂存区合计 {staging_count} 条")

    tomb = "# 已失效\n\n> 退役规则的墓碑。**不硬删**：写清失效原因、证据锚点、判定日期。\n\n（暂无）\n"
    (TREE / "已失效.md").write_text(tomb, encoding="utf-8")
    written.add(Path("已失效.md"))

    stale = sorted(before - written)
    if stale:
        print(f"[渲染] ⚠ 残留旧文件 {len(stale)} 个 —— **必须清掉**，否则主题合计会被虚高"
              f"（实测：残留 5 个旧阶段文件把 11,511 虚报成 24,357）")
        for s in stale[:10]:
            print(f"[渲染]   {s}")
        print("[渲染] 清理命令（走回收站，禁硬删）：")
        print(r'[渲染]   $rb="$env:USERPROFILE\.dsh\skills\dev-hygiene\scripts\Remove-ToRecycleBin.ps1"')
        for s in stale:
            print(f'[渲染]   pwsh -NoProfile -File $rb -Path "{TREE / s}"')
    if all_warns:
        print(f"[渲染] ⚠ WARN {len(all_warns)} 条：")
        for w in all_warns[:20]:
            print(f"[渲染]   {w}")
    print(f"[渲染] 输出目录：{TREE}")
    return TREE


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
