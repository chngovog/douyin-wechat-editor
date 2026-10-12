from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from integrity import inside, sha256, fingerprint, content_checks, final_checks, check_source
from policies import WORD_POLICY, VISUAL_POLICY, FRAME_POLICY, DELIVERY_POLICY, EDITORIAL_POLICY, count_report, count_errors


ACCOUNTS = {"digital", "basketball", "dream", "entertainment"}
HARD_GATE_ACCOUNTS = {"basketball", "dream"}


class ArticleError(RuntimeError):
    pass


def resolve_path(root: Path, value: str) -> Path:
    return inside(root, value)


def read_job(path: Path) -> tuple[dict[str, Any], Path]:
    path = path.resolve()
    if not path.is_file():
        raise ArticleError(f"找不到任务文件: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig")), path


def write_job(path: Path, job: dict[str, Any]) -> None:
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> None:
    if args.account not in ACCOUNTS:
        raise ArticleError(f"未知账号: {args.account}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,119}", args.slug):
        raise ArticleError("slug必须为2-120位字母数字/下划线/连字符，不能包含路径")
    target = Path(args.project_root).resolve() / args.slug
    if target.exists():
        raise ArticleError(f"任务目录已存在: {target}")
    for item in ("source", "assets/frames", "assets/collages", "assets/covers", "analysis", "deliver"):
        (target / item).mkdir(parents=True, exist_ok=True)
    job = {
        "schema_version": 8,
        "word_count_policy": WORD_POLICY,
        "visual_policy": VISUAL_POLICY,
        "delivery_policy": DELIVERY_POLICY,
        "editorial_policy": EDITORIAL_POLICY,
        "editorial_records": {"content_value": "analysis/content-value-review.md", "voice": "analysis/voice-review.md"},
        "source_dedup": {"checked_at": "", "scope": "", "video_id": "", "canonical_url": "", "event_summary": "", "matched_jobs": [], "decision": "pending", "reason": ""},
        "account": args.account,
        "slug": args.slug,
        "source": {"type": "video", "path": "", "creator": "", "claim": "", "page_url": "", "published_at": "", "event_date": "", "checked_at": "", "rights_status": "research-only; permission unconfirmed"},
        "identity": {},
        "research": {"mode": "supplied", "tabs": [], "candidates": [], "mute_checked": False, "freshness_checked_at": "", "selected_reason": ""},
        "workflow": {"stage": "initialized", "next_action": "Bind the source video and verify evidence", "timings": []},
        "build": {},
        "title": args.title,
        "graphic_title": args.graphic_title or "",
        "title_strategy": {
            "core_entity": "", "concrete_change": "", "reader_payoff": "",
            "decisive_detail": "", "tension": "", "stakes": "", "hook_type": "",
            "debate_sides": [], "comment_trigger": "",
            "article_question_type": "", "graphic_question_type": "",
            "article_question_answer": "", "graphic_question_answer": "",
            "answer_in_lead": False, "question_mark_checked": False,
            "question_pattern_overlap_checked": False,
            "topic_tension_checked": False, "closed_question_rejected": False,
            "flatness_checked": False, "thumbnail_punch_checked": False,
            "article_model": "", "graphic_model": "", "selected_reason": "",
            "evidence_basis": [], "search_terms": [], "recent_title_overlap_checked": False,
            "cover_text_relation": "", "article_candidates": [], "graphic_candidates": []
        },
        "cover": {
            "generator": "imagegen", "mode": "built-in", "text_method": "pending",
            "evidence_use": False, "prompts": {"vertical_3_4": "", "horizontal_2_35_1": ""},
            "source_lock": args.account == "dream", "added_nontext_visuals": [], "side_by_side_checked": False,
            "text": "", "text_candidates": [], "hook_type": "", "question_type": "",
            "question_mark_checked": False, "visual_concepts": [],
            "visual_concept": "", "visual_tension": "", "thumbnail_hook_checked": False,
            "recent_cover_overlap_checked": False, "prompt": "", "source_strategy": "",
            "source_frame": "", "source_timestamp": "", "source_exception": "",
            "subject_method": "", "typography_style": "exaggerated-editorial-headline",
            "cover_square_crop_checked": False,
            "outputs": {"vertical_3_4": "assets/covers/封面_竖版_3比4.png", "horizontal_2_35_1": "assets/covers/封面_横版_2.35比1.png"}
        },
        "originality": {
            "source_type": "video", "source_duration_seconds": 0, "source_summary": "",
            "structure_model": "", "verifiable_facts": [], "independent_additions": [],
            "comparisons": [], "mechanism_or_impact": "", "reader_decision": "",
            "recent_similarity_checked": False, "distinct_from_recent": "",
            "publish_decision": "hold", "hold_or_merge_reason": "待补证据"
        },
        "visual_plan": {
            "recommended_visible_units": "exactly-2", "planned_visible_units": 2,
            "preferred_structure": "2 distinct annotated single-column collages",
            "collage_frame_policy": FRAME_POLICY,
            "preferred_frames_per_collage": "2-3; maximum 4",
            "collage_export_budget": {"maximum_edge_px": 4096, "maximum_bytes": 3145728, "basis": "local-conservative-budget-not-WeChat-limit"},
            "annotation_review": "analysis/visual-review.md",
            "direct_frame_units": 0, "collage_units": 2,
            "detail_or_comparison_units": 0, "imagegen_highlight_units": 0,
            "real_evidence_units": 0, "unique_source_frames": 0,
            "below_recommendation_reason": "", "structure_exception_reason": ""
        },
        "imagegen_highlights": [],
        "digital_decision": {},
        "blocks": [], "sources": [], "evidence_items": [], "collage_manifests": [],
        "single_frame_exception": "", "output": "deliver/公众号文章_inline.html",
        "preview": None, "layout_report": "analysis/mobile-layout-check.json",
        "evidence": {"ledger_output": "evidence_ledger.md"},
        "qa": {
            "target_visible_chars": 440, "minimum_visible_chars": 400, "maximum_visible_chars": 500,
            "maximum_cjk": 500,
            "recommended_minimum_visible_units": 2, "recommended_maximum_visible_units": 2,
            "minimum_headings": 0,
            "require_mobile_preview": False, "require_mobile_layout_check": True, "require_title_strategy": True,
            "require_imagegen_cover": True, "require_cover_variants": True,
            "require_imagegen_text": True, "require_cover_source_record": True,
            "require_originality_gate": True, "minimum_verifiable_facts": 6,
            "minimum_independent_additions": 2, "minimum_comparisons": 1,
            "require_digital_decision_gate": args.account == "digital",
            "require_imagegen_highlight_record": True,
            "short_body_reason": "", "length_override_user_request": "",
            "review": {}
        }
    }
    write_job(target / "article-job.json", job)
    print(f"新任务: {target}")


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def render_block(root: Path, block: dict[str, Any], embed_images=True) -> str:
    kind = block.get("type")
    text = html.escape(str(block.get("text", "")))
    if kind == "lead":
        return f'<p class="lead">{text}</p>'
    if kind == "paragraph":
        return f'<p>{text}</p>'
    if kind == "heading":
        return f'<h2>{text}</h2>'
    if kind == "question":
        return f'<p class="question">{text}</p>'
    if kind == "notice":
        return f'<div class="notice">{text}</div>'
    if kind == "figure":
        image = resolve_path(root, str(block.get("src", "")))
        if embed_images and not image.is_file():
            raise ArticleError(f"配图不存在: {image}")
        visual = html.escape(str(block.get("visual", "direct-video-frame")), quote=True)
        attrs = [f'data-visual="{visual}"']
        for src, dest in (("source_timestamp", "data-source-timestamp"), ("frame_count", "data-frame-count"), ("collage_manifest", "data-collage-manifest"), ("imagegen_purpose", "data-imagegen-purpose"), ("source_references", "data-source-references")):
            value = block.get(src)
            if value not in (None, ""):
                attrs.append(f'{dest}="{html.escape(str(value), quote=True)}"')
        cap = html.escape(str(block.get("caption", "")))
        image_src = data_uri(image) if embed_images else ""
        return f'<figure {" ".join(attrs)}><img src="{image_src}" alt="{cap}"><figcaption>{cap}</figcaption></figure>'
    raise ArticleError(f"不支持的正文块: {kind}")


def build_html(job: dict[str, Any], root: Path, embed_images=True) -> str:
    blocks = "\n".join(render_block(root, item, embed_images) for item in job.get("blocks", []))
    source_items = []
    source_records = job.get("sources") or job.get("evidence", {}).get("external_sources", [])
    for item in source_records:
        name = html.escape(str(item.get("name") or item.get("title") or item.get("url", "来源")))
        raw_url = str(item.get("url", ""))
        if raw_url and not raw_url.startswith(("https://", "http://")):
            raise ArticleError("资料来源仅支持http/https链接")
        url = html.escape(raw_url, quote=True)
        source_items.append(f'<li><a href="{url}">{name}</a></li>' if url else f"<li>{name}</li>")
    sources = f'<section class="sources"><h3>资料来源</h3><ol>{"".join(source_items)}</ol></section>' if source_items else ""
    title = html.escape(str(job.get("title", "")))
    creator = html.escape(str(job.get("source", {}).get("creator", "")))
    account_label = {
        "digital": "手机数码观察",
        "basketball": "篮球热爱者",
        "dream": "梦幻西游玩家",
        "entertainment": "娱乐观察",
    }.get(str(job.get("account", "")), "公众号编辑")
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f4f6;color:#20242a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}main{{max-width:720px;margin:0 auto;background:#fff;padding:28px 20px 42px}}h1{{font-size:28px;line-height:1.35;margin:0 0 10px;color:#111827;overflow-wrap:anywhere;word-break:break-word}}.byline{{font-size:13px;color:#89909a;margin-bottom:25px}}p{{font-size:17px;line-height:1.9;margin:18px 0;letter-spacing:.02em}}.lead{{font-size:19px;line-height:1.75;font-weight:650;border-left:5px solid #ef3f3f;padding:12px 16px;background:#fff7f7}}.question{{margin-top:26px;padding:15px 16px;border-radius:7px;background:#fff7ed;color:#9a3412;font-weight:700}}.notice{{padding:13px 15px;background:#f5f5f5;border-left:4px solid #f59e0b}}h2{{font-size:21px;margin:30px 0 10px;padding-left:10px;border-left:4px solid #f59e0b}}figure{{margin:23px 0}}img{{display:block;width:100%;height:auto;border-radius:8px}}figcaption{{font-size:13px;line-height:1.6;color:#737b86;text-align:center;margin-top:8px}}.sources{{margin-top:32px;padding-top:18px;border-top:1px solid #e5e7eb;color:#6b7280;font-size:13px}}.sources h3{{font-size:15px;color:#4b5563}}.sources li{{margin:7px 0;line-height:1.5}}a{{color:#576b95;text-decoration:none}}@media(max-width:480px){{main{{padding:22px 16px 36px}}h1{{font-size:25px}}p{{font-size:16.5px}}}}
</style></head><body><main><h1>{title}</h1><div class="byline">{account_label} · 素材来源：{creator}</div>{blocks}{sources}</main></body></html>'''


def build_ledger(job: dict[str, Any]) -> str:
    lines = [f"# 证据台账｜{job.get('title','')}", "", f"- 账号：{job.get('account','')}", f"- 原视频：{job.get('source',{}).get('path','')}", "", "## 证据项", ""]
    items = job.get("evidence_items", [])
    for index, item in enumerate(items, 1):
        lines += [f"### {index}. {item.get('claim','')}", f"- 类型：{item.get('type','')}", f"- 证据：{item.get('evidence','')}", f"- 边界：{item.get('boundary','')}", ""]
    if not items:
        evidence = job.get("evidence", {})
        lines += ["## 核心事件", "", str(evidence.get("core_event", "")), "", "## 视频证据", ""]
        for index, item in enumerate(evidence.get("rows", []), 1):
            lines += [f"### {index}. {item.get('timestamp','')}", f"- 观察：{item.get('observation','')}", f"- 风险：{item.get('risk','')}", f"- 安全写法：{item.get('article_use','')}", ""]
        lines += ["## 外部核验", ""]
        for item in evidence.get("external_sources", []):
            lines.append(f"- [{item.get('title', item.get('class','来源'))}]({item.get('url','')})：{item.get('claim','')}")
        lines += ["", "## 风险说明", ""] + [f"- {item}" for item in evidence.get("risks", [])]
        originality = job.get("originality", {})
        lines += ["", "## 原创性", "", f"- 结构模型：{originality.get('structure_model','')}", f"- 机制/影响：{originality.get('mechanism_or_impact','')}", f"- 读者判断：{originality.get('reader_decision','')}"]
    if job.get("single_frame_exception"):
        lines += ["", "## 单帧例外", job["single_frame_exception"]]
    lines += ["", "## 完整编辑记录（仅内部，不进入正文）", "```json",
              json.dumps({k: job.get(k) for k in ("identity", "source", "originality", "digital_decision", "title_strategy", "sources")}, ensure_ascii=False, indent=2), "```"]
    return "\n".join(lines)


def cmd_render(args: argparse.Namespace) -> None:
    job, path = read_job(Path(args.job)); root = path.parent
    errors = content_checks(job, root)
    validate_titles(job, errors)
    if errors: raise ArticleError("预检失败: " + "; ".join(errors))
    input_fingerprint = fingerprint(job, root)
    output = resolve_path(root, str(job.get("output"))); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_html(job, root), encoding="utf-8-sig")
    ledger = resolve_path(root, str(job.get("evidence", {}).get("ledger_output", "evidence_ledger.md")))
    ledger.write_text(build_ledger(job), encoding="utf-8-sig")
    job["build"] = {"input_fingerprint": input_fingerprint, "html_sha256": sha256(output), "ledger_sha256": sha256(ledger)}
    job["workflow"]["stage"] = "rendered"
    job["qa"]["review"] = {}
    write_job(path, job)
    print(f"本地待质检 HTML: {output}"); print(f"证据台账: {ledger}")
    if job.get('word_count_policy') == WORD_POLICY:
        report = word_report(job, root)
        report_path = root / 'analysis/word-count.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if count_errors(report):
            raise ArticleError('; '.join(count_errors(report)))


def word_report(job, root):
    expected = build_html(job, root, embed_images=False)
    output = resolve_path(root, job['output'])
    report = count_report(output.read_text(encoding='utf-8-sig') if output.is_file() else expected, expected)
    report['html_sha256'] = sha256(output) if output.is_file() else None
    return report


def cmd_count(args):
    job, path = read_job(Path(args.job))
    report = word_report(job, path.parent)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if count_errors(report):
        raise ArticleError('; '.join(count_errors(report)))


def cmd_check_layout(args):
    job, path = read_job(Path(args.job)); root = path.parent
    output = resolve_path(root, job['output'])
    if not output.is_file() or job.get('build', {}).get('input_fingerprint') != fingerprint(job, root):
        raise ArticleError('请先重新render，不能检查过期HTML')
    if job['build'].get('html_sha256') != sha256(output):
        raise ArticleError('HTML已变化，请重新render')
    report = resolve_path(root, job.get('layout_report', 'analysis/mobile-layout-check.json'))
    renderer = Path(__file__).with_name('render_local_html_mobile.js')
    result = subprocess.run([os.environ.get('NODE', 'node'), str(renderer), '--layout-check', str(output), str(report)], check=False)
    if result.returncode:
        raise ArticleError('375px无截图排版检查失败；查看layout报告')
    job['build']['layout_sha256'] = sha256(report)
    job['workflow']['stage'] = 'layout-checked'
    write_job(path, job)
    print(f'375px无截图排版检查: {report}；仍需图片与内容目视')


def cmd_preview(args: argparse.Namespace) -> None:
    job, path = read_job(Path(args.job)); root = path.parent
    if job.get('delivery_policy') == DELIVERY_POLICY:
        return cmd_check_layout(args)
    output = resolve_path(root, str(job.get("output"))); preview = resolve_path(root, str(job.get("preview")))
    if not output.is_file(): raise ArticleError("请先运行 render")
    if job.get("build", {}).get("input_fingerprint") != fingerprint(job, root):
        raise ArticleError("输入已变化，请先重新render")
    if job["build"].get("html_sha256") != sha256(output):
        raise ArticleError("HTML已变化，请重新render")
    renderer = Path(__file__).with_name("render_local_html_mobile.js")
    preview.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([os.environ.get("NODE", "node"), str(renderer), str(output), str(preview)], cwd=renderer.parent, check=False)
    if result.returncode: raise ArticleError("移动端预览失败")
    job["build"]["preview_sha256"] = sha256(preview)
    job["workflow"]["stage"] = "previewed"
    write_job(path, job)
    print(f"移动端预览: {preview}")


def image_size(path: Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(path) as image: return image.size


def complete(records: Any, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [x for x in records if isinstance(x, dict) and all(str(x.get(k, "")).strip() for k in fields)] if isinstance(records, list) else []


def validate_titles(job: dict[str, Any], errors: list[str]) -> None:
    title = str(job.get("title", "")).strip(); graphic = str(job.get("graphic_title", "")).strip(); s = job.get("title_strategy", {})
    strict_topic = int(job.get("schema_version", 0) or 0) >= 7
    if not title:
        errors.append("缺少 title")
    elif not title.endswith("？"):
        errors.append("title 必须为疑问/反问句并以中文全角？结尾")
    if not graphic or len(graphic) > 20:
        errors.append("graphic_title 缺失或超过20字")
    elif not graphic.endswith("？"):
        errors.append("graphic_title 必须为疑问/反问句并以中文全角？结尾")
    required_text = ["core_entity","concrete_change","reader_payoff","decisive_detail","tension","stakes","hook_type","article_model","graphic_model","selected_reason","cover_text_relation","article_question_type","graphic_question_type","article_question_answer","graphic_question_answer"]
    if strict_topic:
        required_text.append("comment_trigger")
    for key in required_text:
        if not str(s.get(key, "")).strip():
            errors.append(f"标题策略缺少 {key}")
    debate_sides = s.get("debate_sides", [])
    if strict_topic and (not isinstance(debate_sides, list) or len([x for x in debate_sides if str(x).strip()]) < 2):
        errors.append("标题策略 debate_sides 至少需要两项具体立场/选择")
    if s.get("article_question_type") == s.get("graphic_question_type") and str(s.get("article_question_type","")).strip():
        errors.append("文章标题与图文标题必须使用不同问句模型")
    if not s.get("evidence_basis"):
        errors.append("标题策略缺少 evidence_basis")
    required_checks = ["recent_title_overlap_checked","question_pattern_overlap_checked","question_mark_checked","answer_in_lead","flatness_checked","thumbnail_punch_checked"]
    if strict_topic:
        required_checks.extend(["topic_tension_checked","closed_question_rejected"])
    for key in required_checks:
        if s.get(key) is not True:
            errors.append(f"标题策略未通过 {key}")
    for key, selected, label in (("article_candidates", title, "文章"),("graphic_candidates",graphic,"图文")):
        candidates=s.get(key,[])
        if len(candidates)<4:
            errors.append(f"{label}标题候选少于4条")
            continue
        models={str(x.get("model","")).strip() for x in candidates if isinstance(x,dict) and str(x.get("model","")).strip()}
        if len(models)<4:
            errors.append(f"{label}标题候选少于4种不同模型")
        if any(not str(x.get("text","")).strip().endswith("？") for x in candidates if isinstance(x,dict)):
            errors.append(f"{label}标题候选必须全部为以全角？结尾的问句/反问句")
        if key == "graphic_candidates" and any(len(str(x.get("text", ""))) > 20 for x in candidates):
            errors.append("图文标题候选也必须不超过20字符")
        hit=[x for x in candidates if x.get("text")==selected]
        minimum_score = 9 if strict_topic else 8
        if not hit or float(hit[0].get("score",0))<minimum_score:
            errors.append(f"{label}最终标题未入选或评分低于{minimum_score}分")
        elif strict_topic and float(hit[0].get("topic_score",0)) != 2:
            errors.append(f"{label}最终标题 topic_score 必须为2分")


def cmd_validate(args: argparse.Namespace) -> None:
    job, path = read_job(Path(args.job)); root=path.parent; errors=[]; warnings=[]
    errors.extend(content_checks(job, root))
    errors.extend(final_checks(job, root))
    output=resolve_path(root,str(job.get("output"))); ledger=resolve_path(root,str(job.get("evidence",{}).get("ledger_output","evidence_ledger.md")))
    if not output.is_file(): errors.append("缺少发布 HTML")
    if job.get('delivery_policy') != DELIVERY_POLICY and not resolve_path(root, str(job.get('preview'))).is_file():
        errors.append('缺少移动端预览')
    if not ledger.is_file(): errors.append("缺少证据台账")
    blocks=job.get("blocks",[]); body="".join(str(x.get("text","")) for x in blocks); cjk=len(re.findall(r"[\u4e00-\u9fff]",body)); qa=job.get("qa",{})
    maximum = int(qa.get("maximum_cjk", 550))
    if job.get('word_count_policy') == WORD_POLICY:
        report = word_report(job, root)
        errors.extend(count_errors(report))
    elif maximum > 550 and not qa.get("length_override_user_request"):
        errors.append("超过550字上限需要用户当前明确长文要求")
    if job.get('word_count_policy') != WORD_POLICY and (cjk > maximum or (cjk < 450 and not qa.get("short_body_reason"))):
        errors.append(f"正文中文字符超出范围且没有合理例外: {cjk}")
    figure_count=sum(1 for x in blocks if x.get("type")=="figure")
    recommended_min=int(qa.get("recommended_minimum_visible_units",3))
    recommended_max=int(qa.get("recommended_maximum_visible_units",4))
    visual_plan=job.get("visual_plan",{})
    if figure_count<recommended_min:
        reason=str(visual_plan.get("structure_exception_reason","")).strip() or str(visual_plan.get("below_recommendation_reason","")).strip()
        suffix=f"；已登记原因：{reason}" if reason else "；未登记 visual_plan.structure_exception_reason"
        warnings.append(f"正文可见配图单元仅 {figure_count} 个，约500字新稿建议约3个，优先1张视频大图+2组拼图{suffix}")
    if figure_count>recommended_max:
        reason=str(visual_plan.get("structure_exception_reason","")).strip()
        suffix=f"；已登记原因：{reason}" if reason else "；未登记 visual_plan.structure_exception_reason"
        warnings.append(f"正文可见配图单元为 {figure_count} 个，已超过约500字新稿的约3图默认{suffix}")
    highlight_blocks=[x for x in blocks if x.get("type")=="figure" and x.get("visual")=="imagegen-highlight-graphic"]
    highlight_records=job.get("imagegen_highlights",[])
    if not isinstance(highlight_records,list):
        errors.append("imagegen_highlights 必须为数组")
        highlight_records=[]
    if highlight_blocks and qa.get("require_imagegen_highlight_record",True):
        if len(highlight_records)!=len(highlight_blocks):
            errors.append("ImageGen正文亮点图数量与 imagegen_highlights 记录不一致")
        real_figure_count=figure_count-len(highlight_blocks)
        if len(highlight_blocks)>=real_figure_count:
            errors.append("ImageGen正文亮点图不得达到或超过真实视频/资料配图单元数量")
        if len(highlight_blocks)>1:
            errors.append("约500字新稿最多1张ImageGen正文亮点图，且应计入约3个正文配图单元")
        for index, block in enumerate(highlight_blocks,1):
            if not str(block.get("imagegen_purpose","")).strip() or not str(block.get("source_references","")).strip():
                errors.append(f"ImageGen正文亮点图{index}缺少用途或源时间点元数据")
            caption=str(block.get("caption",""))
            if "ImageGen" not in caption or "不作为事实证据" not in caption:
                errors.append(f"ImageGen正文亮点图{index}缺少非证据披露图注")
        required=("path","purpose","prompt","mode","source_frames","source_timestamps","verified_highlights","exact_text","caption_disclosure")
        for index, record in enumerate(highlight_records,1):
            if not isinstance(record,dict) or any(not record.get(key) for key in required):
                errors.append(f"imagegen_highlights 第{index}条记录不完整")
                continue
            if record.get("text_checked") is not True or record.get("subject_checked") is not True or record.get("evidence_use") is not False:
                errors.append(f"imagegen_highlights 第{index}条未通过文字/主体/非证据检查")
            asset=resolve_path(root,str(record.get("path","")))
            if not asset.is_file():
                errors.append(f"ImageGen正文亮点图文件不存在: {asset}")
    validate_titles(job,errors)
    cover=job.get("cover",{})
    for key in ("text","prompt","source_strategy","source_frame","source_timestamp","subject_method","typography_style","visual_concept","visual_tension","hook_type","question_type"):
        if not str(cover.get(key,"" )).strip(): errors.append(f"封面记录缺少 {key}")
    if str(cover.get("text","")).strip() and not str(cover.get("text","")).strip().endswith("？"):
        errors.append("cover.text 必须为疑问/反问句并以中文全角？结尾")
    if any(not str(x).strip().endswith("？") for x in cover.get("text_candidates",[]) if str(x).strip()):
        errors.append("cover.text_candidates 必须全部为以全角？结尾的问句/反问句")
    if cover.get("generator")!="imagegen" or cover.get("text_method")!="imagegen-verified": errors.append("封面必须为 ImageGen 原生文字")
    if len(cover.get("text_candidates",[]))<3 or len(cover.get("visual_concepts",[]))<2: errors.append("封面短句或视觉概念候选不足")
    for key in ("thumbnail_hook_checked","recent_cover_overlap_checked","cover_square_crop_checked","question_mark_checked"):
        if cover.get(key) is not True: errors.append(f"封面未通过 {key}")
    for key,ratio in (("vertical_3_4",.75),("horizontal_2_35_1",2.35)):
        p=resolve_path(root,str(cover.get("outputs",{}).get(key,"")))
        if not p.is_file(): errors.append(f"缺少封面 {key}")
        else:
            w,h=image_size(p)
            if abs(w/h-ratio)>.025: errors.append(f"封面比例错误 {key}: {w}x{h}")
    o=job.get("originality",{})
    if len(complete(o.get("verifiable_facts",[]),("claim","evidence","article_use")))<6: errors.append("完整可核验事实不足6条")
    additions=complete(o.get("independent_additions",[]),("claim","type","source","verification","article_use"))
    if len(additions)<2 or not any(x.get("independently_verifiable") is True for x in additions): errors.append("视频外独立增量不足或不可独立核验")
    if len(complete(o.get("comparisons",[]),("subject","baseline","finding","evidence")))<1: errors.append("有效比较不足")
    for key in ("source_summary","structure_model","mechanism_or_impact","reader_decision","distinct_from_recent"):
        if not str(o.get(key,"" )).strip(): errors.append(f"原创性记录缺少 {key}")
    if o.get("recent_similarity_checked") is not True or o.get("publish_decision")!="publish": errors.append("原创性门槛未批准独立发布")
    from audit_title_hooks import audit
    title_errors, title_warnings = audit(path)
    errors.extend(title_errors)
    warnings.extend(title_warnings)
    if title_warnings and not job.get("qa", {}).get("review", {}).get("title_audit_notes"):
        errors.append("标题启发式提示需要实际语义复核并填写title_audit_notes，不能只匹配词库")
    for warning in warnings: print(f"[WARN] {warning}",file=sys.stderr)
    if errors:
        print("[FAIL] 公众号文章验证",file=sys.stderr)
        for error in errors: print(f"- {error}",file=sys.stderr)
        raise SystemExit(2)
    job["workflow"]["stage"] = "validated-local"
    new_delivery = job.get('delivery_policy') == DELIVERY_POLICY
    job["workflow"]["next_action"] = f"Deliver {'three' if new_delivery else 'four'} links; not uploaded or published"
    write_job(path, job)
    delivered = {'article': job['output'], **cover['outputs']}
    if not new_delivery:
        delivered['mobile_preview'] = job['preview']
    manifest = {k: {'path': v, 'sha256': sha256(resolve_path(root, v))} for k, v in delivered.items()}
    resolve_path(root, 'deliver/delivery-manifest.json').write_text(json.dumps({'files_required': len(delivered), 'files': manifest, 'platform_status': 'not uploaded or published'}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[PASS] 公众号文章本地验证: {output}")
    if job.get('word_count_policy') == WORD_POLICY:
        print(f"- 完整正文可见字符: {report['body_visible_chars']}；含标题: {report['copy_all_visible_chars']}；本地估算，微信未核验")
    else:
        print(f'- 正文中文字符: {cjk}')
    print(f"- 正文可见配图单元: {figure_count}")


def cmd_status(args: argparse.Namespace) -> None:
    job, path = read_job(Path(args.job))
    report = {"account": job.get("account"), "slug": job.get("slug"), "workflow": job.get("workflow"),
              "publish_decision": job.get("originality", {}).get("publish_decision"),
              "source_errors": check_source(job, path.parent), "build": job.get("build", {})}
    try: report["render_current"] = fingerprint(job, path.parent) == job.get("build", {}).get("input_fingerprint")
    except (OSError, ValueError, KeyError): report["render_current"] = False
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description="微信公众号文章统一生成器"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("init"); p.add_argument("--project-root",required=True); p.add_argument("--slug",required=True); p.add_argument("--account",required=True); p.add_argument("--title",default=""); p.add_argument("--graphic-title",default=""); p.set_defaults(func=cmd_init)
    for name,func in (("render",cmd_render),("count",cmd_count),("check-layout",cmd_check_layout),("preview",cmd_preview),("validate",cmd_validate),("status",cmd_status)):
        p=sub.add_parser(name); p.add_argument("job"); p.set_defaults(func=func)
    return parser


def main() -> None:
    try:
        args = build_parser().parse_args(); args.func(args)
    except (ArticleError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[ERROR] {exc}",file=sys.stderr); raise SystemExit(2)


if __name__ == "__main__": main()
