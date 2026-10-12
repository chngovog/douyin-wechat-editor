"""Local consistency checks. These do not establish factual truth or copyright."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from policies import VISUAL_POLICY, FRAME_POLICY, DELIVERY_POLICY, EDITORIAL_POLICY


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inside(root: Path, value: str) -> Path:
    if not str(value).strip():
        raise ValueError('empty asset/output path')
    root = root.resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f'path must stay inside task directory: {value}')
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def seconds(value: str | float) -> float:
    parts = str(value).split(':')
    if not 1 <= len(parts) <= 3:
        raise ValueError(f'invalid timestamp: {value}')
    total = 0.0
    for part in parts:
        total = total * 60 + float(part)
    if not 0 <= total < float('inf'):
        raise ValueError(f'invalid timestamp: {value}')
    return total


def check_source(job: dict, root: Path) -> list[str]:
    errors = []
    source = job.get('source', {})
    if job.get('account') not in {'digital', 'basketball', 'dream', 'entertainment'}:
        errors.append('unknown account')
    if root.name != job.get('slug'):
        errors.append('task directory and slug do not match')
    for key in ('creator', 'claim', 'path', 'sha256', 'duration_seconds', 'rights_status'):
        if not source.get(key):
            errors.append(f'source.{key} missing')
    identity = job.get('identity', {})
    for key, actual in (('account', job.get('account')), ('slug', job.get('slug')),
                        ('source_sha256', source.get('sha256'))):
        if not actual or identity.get(key) != actual:
            errors.append(f'bound identity mismatch: {key}')
    try:
        video = inside(root, source.get('path', ''))
        if not video.is_file() or sha256(video) != source.get('sha256'):
            errors.append('source video missing or hash changed; do not reuse old evidence')
        if float(source.get('duration_seconds', 0)) <= 0:
            errors.append('source duration must be positive')
    except (ValueError, TypeError, OSError) as exc:
        errors.append(str(exc))
    return errors


def check_frame(job: dict, root: Path, value: str, timestamp=None) -> dict:
    frame = inside(root, value)
    record = read_json(frame.with_suffix('.frame.json'))
    if sha256(frame) != record.get('sha256'):
        raise ValueError(f'frame hash changed: {value}')
    if record.get('source_sha256') != job['source']['sha256']:
        raise ValueError(f'frame belongs to another source: {value}')
    if not 0 <= float(record['seconds']) <= float(job['source']['duration_seconds']):
        raise ValueError(f'frame timestamp out of range: {value}')
    if timestamp is not None and abs(seconds(timestamp) - float(record['seconds'])) > .051:
        raise ValueError(f'frame timestamp mismatch: {value}')
    return record


def fingerprint(job: dict, root: Path) -> str:
    """Bind rendered content to job fields and actual asset bytes, not mtimes."""
    stable = json.loads(json.dumps(job))
    stable.pop('build', None)
    stable.pop('workflow', None)
    stable.get('qa', {}).pop('review', None)
    files = set()
    for block in job.get('blocks', []):
        if block.get('type') == 'figure':
            files.add(block['src'])
            if block.get('collage_manifest'):
                files.add(block['collage_manifest'])
    files.update(job.get('cover', {}).get('outputs', {}).values())
    files.update(job.get('collage_manifests', []))
    if job.get('editorial_policy') == EDITORIAL_POLICY:
        files.update(job.get('editorial_records', {}).values())
    if job.get('visual_policy') == VISUAL_POLICY:
        files.add(job.get('visual_plan', {}).get('annotation_review', 'analysis/visual-review.md'))
    hashes = {name: sha256(inside(root, name)) for name in sorted(files)}
    encoded = json.dumps({'job': stable, 'assets': hashes}, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def content_checks(job: dict, root: Path) -> list[str]:
    errors = check_source(job, root)
    if job.get('editorial_policy') == EDITORIAL_POLICY:
        dedup = job.get('source_dedup', {})
        if dedup.get('decision') not in ('unused', 'explicit-revision') or not all(dedup.get(k) for k in ('checked_at', 'scope', 'event_summary', 'reason')):
            errors.append('full-history source/event dedup audit missing or unresolved')
        for key in ('content_value', 'voice'):
            try:
                note = inside(root, job.get('editorial_records', {}).get(key, ''))
                if len(note.read_text(encoding='utf-8').strip()) < 40:
                    errors.append(f'actual {key} review notes required')
            except (OSError, ValueError) as exc:
                errors.append(f'{key} review missing: {exc}')
    o = job.get('originality', {})
    if o.get('publish_decision') != 'publish':
        errors.append('hold/merge job cannot produce a standalone release HTML')
    source_duration = float(job.get('source', {}).get('duration_seconds') or 0)
    if o.get('source_duration_seconds') != source_duration:
        errors.append('originality duration differs from bound video')
    adds = o.get('independent_additions', [])
    needed = 3 if job.get('account') == 'dream' and source_duration <= 45 else 2
    if len(adds) < needed:
        errors.append(f'at least {needed} independent additions required')
    facts = o.get('verifiable_facts', [])
    if len(facts) < 6 or any(not all(r.get(k) for k in ('claim', 'evidence', 'article_use')) for r in facts):
        errors.append('six complete verifiable facts required before render')
    if any(not all(r.get(k) for k in ('claim', 'type', 'source', 'verification', 'article_use')) for r in adds) or not any(r.get('independently_verifiable') is True for r in adds):
        errors.append('independent additions incomplete or unverifiable')
    comparisons = o.get('comparisons', [])
    if not comparisons or any(not all(r.get(k) for k in ('subject', 'baseline', 'finding', 'evidence')) for r in comparisons):
        errors.append('a complete meaningful comparison required before render')
    for key in ('source_summary', 'structure_model', 'mechanism_or_impact', 'reader_decision', 'distinct_from_recent'):
        if not o.get(key):
            errors.append(f'originality.{key} missing')
    if o.get('recent_similarity_checked') is not True:
        errors.append('recent content comparison not reviewed')
    for records, key in ((o.get('verifiable_facts', []), 'claim'), (adds, 'claim')):
        vals = [str(item.get(key, '')).strip() for item in records]
        if len(vals) != len(set(vals)):
            errors.append('duplicate fact/addition claims')
    if not job.get('evidence_items'):
        errors.append('evidence_items required')
    if job.get('account') == 'digital':
        d = job.get('digital_decision', {})
        for key in ('conditional_decision', 'target_users', 'non_target_users', 'checked_at',
                    'basis', 'title_answer', 'coverage_note'):
            if not d.get(key):
                errors.append(f'digital_decision.{key} required')
        if d.get('coverage_complete') is not True:
            errors.append('digital decision coverage incomplete')
        for key, count, fields in (('subjects', 2, ('name', 'basis', 'evidence')),
                                    ('dimensions', 3, ('name', 'finding', 'evidence'))):
            rows = d.get(key, [])
            if len(rows) < count or any(not all(row.get(k) for k in fields) for row in rows):
                errors.append(f'digital_decision.{key} incomplete')
        if not any(s.get('class') == 'official-primary' and s.get('url') for s in job.get('sources', [])):
            errors.append('digital requires an official-primary source')
    research = job.get('research', {})
    if research.get('mode') == 'autonomous':
        tabs = research.get('tabs', [])
        if len(tabs) != 4 or len({str(t.get('id')) for t in tabs}) != 4:
            errors.append('autonomous workflow needs four distinct new research tabs')
        if len(research.get('candidates', [])) < 3:
            errors.append('autonomous candidate shortlist missing')
        if not research.get('freshness_checked_at') or not research.get('selected_reason'):
            errors.append('autonomous freshness/selection review missing')
        if research.get('mute_checked') is not True:
            errors.append('browser mute not verified')
    for key in ('article_candidates', 'graphic_candidates'):
        for candidate in job.get('title_strategy', {}).get(key, []):
            if not candidate.get('evidence_basis') or candidate.get('topic_tension_checked') is not True or candidate.get('closed_question_rejected') is not True:
                errors.append(f'{key}: candidate evidence/topic review missing')
    cover = job.get('cover', {})
    if cover.get('generator') != 'imagegen' or cover.get('text_method') != 'imagegen-verified':
        errors.append('native ImageGen cover text required before render')
    if cover.get('evidence_use') is not False:
        errors.append('cover is packaging, not evidence')
    if job.get('account') == 'dream':
        if cover.get('source_lock') is not True or cover.get('added_nontext_visuals') != []:
            errors.append('Dream cover source lock missing')
        if cover.get('side_by_side_checked') is not True:
            errors.append('Dream cover requires side-by-side source review')
    outputs = list(cover.get('outputs', {}).values())
    if len(outputs) != 2 or len(set(outputs)) != 2:
        errors.append('two distinct cover paths required')
    if not all(cover.get('prompts', {}).get(k) for k in ('vertical_3_4', 'horizontal_2_35_1')):
        errors.append('actual per-variant ImageGen prompts required')
    blocks = job.get('blocks', [])
    figures = [b for b in blocks if b.get('type') == 'figure']
    visual_plan = job.get('visual_plan', {})
    annotated = job.get('visual_policy') == VISUAL_POLICY
    compact = visual_plan.get('collage_frame_policy') == FRAME_POLICY
    if visual_plan.get('planned_visible_units') != len(figures):
        errors.append('visual plan count differs from actual figures')
    if len(figures) not in (2, 3, 4) and not (len(figures) == 1 and job.get('single_frame_exception')):
        errors.append('body requires 2-4 visible figure units')
    n_direct = sum(b.get('visual') == 'direct-video-frame' for b in figures)
    n_collage = sum(b.get('visual') == 'video-evidence-collage' for b in figures)
    exception = job.get('single_frame_exception', '')
    if annotated and (len(figures) != 2 or n_collage != 2):
        errors.append('new visual policy requires exactly two annotated collages')
    if not annotated and not (n_direct == 1 and n_collage == 2 and len(figures) == 3) and not visual_plan.get('structure_exception_reason'):
        errors.append('non-default visual structure requires reason')
    if not annotated and job.get('account') in ('dream', 'basketball') and not (n_direct and n_collage):
        if len(exception) < 12 or not any(b.get('visual') == 'single-frame-exception' for b in figures):
            errors.append('Dream/basketball need direct frame + collage or documented single-frame exception')
    previous_collage = False
    all_frame_hashes = set()
    collage_claims = set()
    if annotated:
        actual_manifests = [b.get('collage_manifest') for b in figures]
        if set(actual_manifests) != set(job.get('collage_manifests', [])) or len(set(actual_manifests)) != 2:
            errors.append('two distinct registered collage manifests required')
        try:
            note = inside(root, visual_plan.get('annotation_review', ''))
            if len(note.read_text(encoding='utf-8').strip()) < 40:
                errors.append('actual 375px visual review required')
        except (OSError, ValueError) as exc:
            errors.append(f'visual review missing: {exc}')
    for block in blocks:
        if block.get('type') != 'figure':
            if block.get('type') in ('paragraph', 'lead') and block.get('text', '').strip():
                previous_collage = False
            continue
        if block.get('src') in outputs:
            errors.append('cover cannot be reused as body evidence')
        visual = block.get('visual')
        try:
            if visual in ('direct-video-frame', 'single-frame-exception'):
                check_frame(job, root, block['src'], block.get('source_timestamp', ''))
            elif visual == 'video-evidence-collage':
                if previous_collage:
                    errors.append('collages need an explanatory paragraph between them')
                previous_collage = True
                manifest = read_json(inside(root, block['collage_manifest']))
                if manifest.get('layout') != 'single-column-original-ratio':
                    errors.append('collage must use single-column original-ratio layout')
                if manifest.get('kind') != 'video-evidence-collage':
                    errors.append('wrong collage kind')
                rows = manifest.get('sources', [])
                lo, hi = (2, 4) if compact else (4, 6)
                if not lo <= len(rows) <= hi or len(rows) != block.get('frame_count') or len(rows) != manifest.get('frame_count'):
                    errors.append(f'collage frame counts must match and be {lo}-{hi}')
                if len({r.get('sha256') for r in rows}) != len(rows):
                    errors.append('collage contains duplicate image hashes')
                if manifest.get('source_sha256') != job.get('source', {}).get('sha256'):
                    errors.append('collage belongs to another video')
                if manifest.get('output') != block['src'] or sha256(inside(root, block['src'])) != manifest.get('output_sha256'):
                    errors.append('collage asset and manifest mismatch')
                if compact:
                    from PIL import Image
                    asset = inside(root, block['src'])
                    with Image.open(asset) as image:
                        if max(image.size) > 4096 or asset.stat().st_size > 3 * 1024 * 1024:
                            errors.append('collage exceeds local 4096px/3MiB export budget')
                if annotated:
                    claim = str(manifest.get('claim', '')).strip()
                    if not claim or claim in collage_claims:
                        errors.append('each collage needs a distinct evidence claim')
                    collage_claims.add(claim)
                    hashes = {r.get('sha256') for r in rows}
                    if hashes & all_frame_hashes:
                        errors.append('duplicate source frames across the two collages')
                    all_frame_hashes.update(hashes)
                    annotations = manifest.get('public_annotations', {})
                    if not annotations.get('title') or not annotations.get('items'):
                        errors.append('actual in-image title and annotation records required')
                    for item in annotations.get('items', []):
                        if (not isinstance(item.get('source_index'), int)
                            or not 1 <= item['source_index'] <= len(rows)
                            or not all(item.get(k) for k in ('text', 'evidence_ref', 'placement'))
                            or item.get('basis') not in ('frame', 'speaker', 'editorial', 'external')):
                            errors.append('in-image annotation record incomplete')
                for row in rows:
                    check_frame(job, root, row['path'], row['timestamp'])
                    if sha256(inside(root, row['path'])) != row.get('sha256') or not row.get('label'):
                        errors.append('collage source/label mismatch')
            elif visual in ('detail-video-frame', 'annotated-video-frame'):
                if not block.get('transform_note'):
                    errors.append('detail/annotation transformation note required')
                check_frame(job, root, block.get('source_frame', ''), block.get('source_timestamp', ''))
            elif visual == 'external-evidence':
                if not block.get('source_id') or not any(s.get('id') == block['source_id'] for s in job.get('sources', [])):
                    errors.append('external figure needs a registered source_id')
            elif visual != 'imagegen-highlight-graphic':
                errors.append(f'unknown figure evidence type: {visual}')
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(f'visual evidence error: {exc}')
    try:
        check_frame(job, root, cover.get('source_frame', ''), cover.get('source_timestamp', ''))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(f'cover reference error: {exc}')
    return errors


def final_checks(job: dict, root: Path) -> list[str]:
    errors = []
    build = job.get('build', {})
    try:
        if build.get('input_fingerprint') != fingerprint(job, root):
            errors.append('inputs changed after render; render + layout/visual check again')
        artifacts = [('html_sha256', job['output']), ('ledger_sha256', job['evidence']['ledger_output'])]
        if job.get('delivery_policy') == DELIVERY_POLICY:
            artifacts.append(('layout_sha256', job['layout_report']))
            report = read_json(inside(root, job['layout_report']))
            if (report.get('html_sha256') != sha256(inside(root, job['output']))
                or report.get('viewport_width') != 375 or report.get('passed') is not True
                or report.get('broken_images') != 0 or report.get('horizontal_overflow') is not False
                or not report.get('checked_at')):
                errors.append('375px layout report missing, failed or stale')
        else:
            artifacts.append(('preview_sha256', job['preview']))
        for field, name in artifacts:
            if build.get(field) != sha256(inside(root, name)):
                errors.append(f'{field} missing or stale')
    except (ValueError, KeyError, OSError) as exc:
        errors.append(str(exc))
    review = job.get('qa', {}).get('review', {})
    for key in ('mobile_375_checked', 'cover_text_checked', 'source_subjects_checked',
                'human_voice_checked', 'facts_checked'):
        if review.get(key) is not True:
            errors.append(f'actual editorial review required: {key}')
    if review.get('input_fingerprint') != build.get('input_fingerprint') or not review.get('checked_at'):
        errors.append('review must refer to current build fingerprint and time')
    try:
        note = inside(root, review.get('notes_path', ''))
        if len(note.read_text(encoding='utf-8').strip()) < 40:
            errors.append('review notes must describe actual evidence and visual checks')
    except (ValueError, OSError) as exc:
        errors.append(f'review notes missing: {exc}')
    return errors
