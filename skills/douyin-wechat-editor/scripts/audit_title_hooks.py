#!/usr/bin/env python3
"""Audit WeChat title and cover-hook records without judging factual truth.

This catches structural flatness and missing editorial review fields. It cannot
verify whether a strong verb or consequence is true; the editor must map every
claim back to the evidence ledger.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FLAT_PHRASES = (
    "值得关注",
    "发生变化",
    "只是第一步",
    "下一课",
    "优势没出来",
    "意味着什么",
    "背后原因",
    "机制解析",
    "深度解析",
)
GENERIC_TOPIC_ENDINGS = (
    "谁付代价",
    "差距在哪",
    "靠什么",
    "还不够",
    "算亮点",
    "真有效",
)
ACTION_WORDS = (
    "停",
    "卡",
    "撕开",
    "反超",
    "守住",
    "打穿",
    "开出",
    "拍进",
    "跌",
    "涨",
    "只剩",
    "被迫",
    "先等",
    "打",
    "开",
    "传球",
    "刷屏",
    "败诉",
    "开庭",
    "爆满",
    "限创",
    "抢",
    "输",
    "赢",
)
CONFLICT_WORDS = (
    "却",
    "但",
    "还不够",
    "不等于",
    "只写",
    "没",
    "先别",
    "反而",
    "代价",
    "风险",
    "门槛",
)
RESULT_WORDS = (
    "结果",
    "后果",
    "代价",
    "值钱",
    "难买",
    "不值",
    "翻车",
    "爆满",
    "限创",
    "停了",
    "开出",
)
REQUIRED_TITLE_STRATEGY = (
    "decisive_detail",
    "tension",
    "stakes",
    "hook_type",
    "article_question_type",
    "graphic_question_type",
    "article_question_answer",
    "graphic_question_answer",
    "answer_in_lead",
    "question_mark_checked",
    "question_pattern_overlap_checked",
    "flatness_checked",
    "thumbnail_punch_checked",
)
REQUIRED_TOPIC_STRATEGY = (
    "comment_trigger",
    "topic_tension_checked",
    "closed_question_rejected",
)
REQUIRED_COVER = (
    "text_candidates",
    "hook_type",
    "question_type",
    "question_mark_checked",
    "visual_concept",
    "visual_tension",
    "thumbnail_hook_checked",
    "recent_cover_overlap_checked",
)


def discover(inputs: list[str]) -> list[Path]:
    roots = [Path(item) for item in inputs] if inputs else [Path.cwd()]
    found: list[Path] = []
    for root in roots:
        if root.is_file():
            found.append(root)
        elif root.is_dir():
            found.extend(root.rglob("article-job.json"))
    return sorted({path.resolve() for path in found})


def count_hooks(text: str) -> tuple[int, list[str]]:
    hooks: list[str] = []
    if re.search(r"\d", text):
        hooks.append("number/detail")
    if any(word in text for word in ACTION_WORDS):
        hooks.append("action/result")
    if any(word in text for word in CONFLICT_WORDS):
        hooks.append("conflict/tradeoff")
    if any(word in text for word in RESULT_WORDS):
        hooks.append("consequence/stake")
    return len(set(hooks)), list(dict.fromkeys(hooks))


def audit(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        job = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"], []

    title = str(job.get("title", "")).strip()
    graphic = str(job.get("graphic_title", "")).strip()
    cover = job.get("cover") if isinstance(job.get("cover"), dict) else {}
    cover_text = str(cover.get("text", "")).strip()
    strategy = (
        job.get("title_strategy")
        if isinstance(job.get("title_strategy"), dict)
        else {}
    )
    strict_topic = int(job.get("schema_version", 0) or 0) >= 7

    if not title:
        errors.append("missing title")
    elif not title.endswith("？"):
        errors.append("title must be a question/rhetorical question ending with full-width ？")
    if not graphic:
        errors.append("missing graphic_title")
    elif len(graphic) > 20:
        errors.append(f"graphic_title exceeds 20 characters ({len(graphic)})")
    elif not graphic.endswith("？"):
        errors.append(
            "graphic_title must be a question/rhetorical question ending with full-width ？"
        )
    elif not 10 <= len(graphic) <= 16:
        warnings.append(
            f"graphic_title length {len(graphic)} is outside preferred 10-16"
        )

    hook_count, hooks = count_hooks(graphic)
    if graphic and hook_count < 2:
        warnings.append(
            "graphic_title has fewer than two machine-visible hook types "
            f"({', '.join(hooks) or 'none'}); perform semantic editorial review"
        )
    flat_hits = [phrase for phrase in FLAT_PHRASES if phrase in graphic]
    if flat_hits:
        warnings.append(
            "graphic_title contains abstract flat phrase(s): " + ", ".join(flat_hits)
        )
    if strict_topic:
        generic_hits = [phrase for phrase in GENERIC_TOPIC_ENDINGS if phrase in graphic]
        if generic_hits:
            warnings.append(
                "graphic_title uses generic topic ending(s): " + ", ".join(generic_hits)
            )

    debate_sides = strategy.get("debate_sides")
    if strict_topic and (not isinstance(debate_sides, list) or len(
        [item for item in debate_sides if str(item).strip()]
    ) < 2):
        warnings.append("title_strategy.debate_sides must contain at least 2 concrete positions")

    for field in REQUIRED_TITLE_STRATEGY:
        if field not in strategy or strategy.get(field) in (None, "", False):
            warnings.append(f"title_strategy.{field} is missing or not confirmed")
    if strict_topic:
        for field in REQUIRED_TOPIC_STRATEGY:
            if field not in strategy or strategy.get(field) in (None, "", False):
                warnings.append(f"title_strategy.{field} is missing or not confirmed")
    if (
        strategy.get("article_question_type")
        and strategy.get("article_question_type") == strategy.get("graphic_question_type")
    ):
        errors.append("article and graphic titles must use different question models")
    for key in ("article_candidates", "graphic_candidates"):
        candidates = strategy.get(key)
        if isinstance(candidates, list):
            models = {
                str(item.get("model", "")).strip()
                for item in candidates
                if isinstance(item, dict) and str(item.get("model", "")).strip()
            }
            if len(models) < 4:
                warnings.append(f"title_strategy.{key} must use at least 4 models")
        if isinstance(candidates, list) and any(
            isinstance(item, dict)
            and str(item.get("text", "")).strip()
            and not str(item.get("text", "")).strip().endswith("？")
            for item in candidates
        ):
            errors.append(f"title_strategy.{key} contains a non-question candidate")
        selected = title if key == "article_candidates" else graphic
        matches = [
            item
            for item in candidates or []
            if isinstance(item, dict) and str(item.get("text", "")).strip() == selected
        ]
        if not matches:
            warnings.append(f"selected title is missing from title_strategy.{key}")
        else:
            try:
                score = float(matches[0].get("score", 0))
                topic_score = float(matches[0].get("topic_score", 0))
            except (TypeError, ValueError):
                score = 0
                topic_score = 0
            minimum_score = 9 if strict_topic else 8
            if score < minimum_score:
                warnings.append(
                    f"selected title in {key} scores below {minimum_score}/10"
                )
            if strict_topic and topic_score < 2:
                warnings.append(f"selected title in {key} has topic_score below 2")

    if not cover_text:
        errors.append("missing cover.text")
    elif not cover_text.endswith("？"):
        errors.append(
            "cover.text must be a question/rhetorical question ending with full-width ？"
        )
    elif len(cover_text) > 14:
        warnings.append(
            f"cover.text length {len(cover_text)} exceeds preferred 6-14"
        )
    if cover_text and cover_text in {title, graphic}:
        warnings.append("cover.text duplicates a selected title verbatim")

    for field in REQUIRED_COVER:
        value = cover.get(field)
        if field == "text_candidates":
            if not isinstance(value, list) or len(value) < 3:
                warnings.append("cover.text_candidates must contain at least 3 options")
            elif any(
                str(item).strip() and not str(item).strip().endswith("？")
                for item in value
            ):
                errors.append("cover.text_candidates must all end with full-width ？")
        elif value in (None, "", False):
            warnings.append(f"cover.{field} is missing or not confirmed")

    visual_concepts = cover.get("visual_concepts")
    if not isinstance(visual_concepts, list) or len(visual_concepts) < 2:
        warnings.append("cover.visual_concepts must contain at least 2 directions")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="article-job.json files or roots")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as a failing audit"
    )
    args = parser.parse_args()
    jobs = discover(args.paths)
    if not jobs:
        print("[FAIL] no article-job.json found")
        return 2

    total_errors = 0
    total_warnings = 0
    for path in jobs:
        errors, warnings = audit(path)
        status = "FAIL" if errors or (args.strict and warnings) else "PASS"
        print(f"[{status}] {path}")
        for item in errors:
            print(f"  ERROR: {item}")
        for item in warnings:
            print(f"  WARN: {item}")
        total_errors += len(errors)
        total_warnings += len(warnings)

    print(
        f"audited={len(jobs)} errors={total_errors} warnings={total_warnings} "
        f"strict={args.strict}"
    )
    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
