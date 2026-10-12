"""Deterministic one-column original-ratio evidence collage, never a cover generator."""
from __future__ import annotations
import argparse
import io
import os
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
from integrity import check_frame, check_source, inside, read_json, sha256, write_json
from policies import VISUAL_POLICY, FRAME_POLICY


def wrap(draw, text, font, width):
    lines = []; line = ''
    for char in str(text):
        if char == '\n' or (line and draw.textlength(line + char, font=font) > width):
            lines.append(line); line = ''
        if char != '\n':
            line += char
    if line:
        lines.append(line)
    return lines


def build(job_path: Path, spec: dict, font_path: str, width=960):
    root = job_path.resolve().parent; job = read_json(job_path)
    errors = check_source(job, root)
    if errors:
        raise ValueError('; '.join(errors))
    rows = spec.get('frames', [])
    compact = job.get('visual_plan', {}).get('collage_frame_policy') == FRAME_POLICY
    annotated = job.get('visual_policy') == VISUAL_POLICY
    lo, hi = (2, 4) if compact else (4, 6)
    if not lo <= len(rows) <= hi:
        raise ValueError(f'select {lo}-{hi} distinct evidence nodes')
    if not spec.get('title') or not spec.get('claim'):
        raise ValueError('collage title and distinct claim required')
    if not 750 <= width <= 2400:
        raise ValueError('width must be 750-2400 pixels')
    title_font = ImageFont.truetype(font_path, round(width * .047))
    label_font = ImageFont.truetype(font_path, round(width * .043))
    pad = round(width * .04); inner = width - pad * 2
    canvas = Image.new('RGB', (width, 10), '#0c141b'); draw = ImageDraw.Draw(canvas)
    header = wrap(draw, spec['title'], title_font, inner)
    height = pad * 2 + len(header) * round(width * .06)
    tiles = []; sources = []; hashes = set(); annotations = []; operations = []
    for index, row in enumerate(rows, 1):
        if not row.get('label') or not row.get('timestamp'):
            raise ValueError('each frame needs label and timestamp')
        check_frame(job, root, row['path'], row['timestamp'])
        source = inside(root, row['path']); digest = sha256(source)
        if digest in hashes:
            raise ValueError('duplicate image content; do not pad evidence')
        hashes.add(digest)
        with Image.open(source) as raw:
            image = raw.convert('RGB')
        original = image.copy()
        focus = row.get('focus')
        zoom = None
        if focus:
            rect = focus.get('rect', [])
            if len(rect) != 4 or not (0 <= rect[0] < rect[2] <= image.width and 0 <= rect[1] < rect[3] <= image.height):
                raise ValueError('focus.rect must be [left,top,right,bottom] inside original pixels')
            if focus.get('shape') not in ('circle', 'box'):
                raise ValueError('focus.shape must be circle or box')
            pen = ImageDraw.Draw(image)
            method = pen.ellipse if focus['shape'] == 'circle' else pen.rectangle
            method(rect, outline='#f34f4f', width=max(2, round(image.width / 250)))
            if focus.get('zoom'):
                zoom = original.crop(tuple(rect))
                scale = min(inner / zoom.width, round(width * .28) / zoom.height)
                zoom = zoom.resize((max(1, round(zoom.width * scale)), max(1, round(zoom.height * scale))), Image.Resampling.LANCZOS)
            operations.append({'source_index': index, 'source_frame': row['path'], **focus})
            if zoom:
                operations[-1]['zoom_output_px'] = list(zoom.size)
        size = (inner, round(image.height * inner / image.width))
        image = image.resize(size, Image.Resampling.LANCZOS)
        label = str(row.get('public_text', '')).strip() if annotated else f'{index} · {row["timestamp"]} | {row["label"]}'
        if annotated and label:
            if row.get('basis') not in ('frame', 'speaker', 'editorial', 'external') or not row.get('evidence_ref'):
                raise ValueError('public_text needs basis and evidence_ref')
            annotations.append({'source_index': index, 'text': label, 'basis': row['basis'],
                'evidence_ref': row['evidence_ref'], 'placement': f'frame {index} lower caption band'})
        lines = wrap(draw, label, label_font, inner - pad)
        if annotated and len(lines) > 2:
            raise ValueError('keep each in-image annotation to at most two lines')
        caption_h = len(lines) * round(width * .058) + pad if lines else 0
        tiles.append((image, lines, caption_h, zoom))
        height += image.height + caption_h + pad + (zoom.height + pad if zoom else 0)
        sources.append(dict(path=row['path'], timestamp=row['timestamp'], label=row['label'], sha256=digest))
    if annotated and not annotations:
        raise ValueError('at least one actual public_text explanation required')
    if compact and max(width, height) > 4096:
        raise ValueError('exceeds local 4096px budget; select fewer useful frames, do not shrink evidence to illegibility')
    canvas = Image.new('RGB', (width, height), '#0c141b'); draw = ImageDraw.Draw(canvas); y = pad
    for line in header:
        draw.text((pad, y), line, font=title_font, fill='#f7f9fa'); y += round(width * .06)
    y += pad
    for image, lines, caption_h, zoom in tiles:
        canvas.paste(image, (pad, y)); y += image.height
        if zoom:
            y += pad
            canvas.paste(zoom, ((width - zoom.width) // 2, y)); y += zoom.height
        draw.rectangle((pad, y, width - pad, y + caption_h), fill='#19232f')
        for idx, line in enumerate(lines):
            draw.text((pad + pad // 2, y + pad // 2 + idx * round(width * .058)), line, font=label_font, fill='#dce5ef')
        y += caption_h + pad
    output = inside(root, spec['output']); manifest = output.with_suffix('.collage.json')
    if output.exists() or manifest.exists():
        raise ValueError('collage exists; use a versioned output name')
    encoded = io.BytesIO()
    fmt = 'JPEG' if output.suffix.lower() in ('.jpg', '.jpeg') else 'PNG'
    canvas.save(encoded, format=fmt, **({'quality': 92, 'subsampling': 0} if fmt == 'JPEG' else {}))
    if compact and len(encoded.getvalue()) > 3 * 1024 * 1024:
        raise ValueError('exceeds local 3MiB budget; use reasonable JPEG or remove redundant nodes')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(encoded.getvalue())
    data = dict(kind='video-evidence-collage', layout='single-column-original-ratio',
        title=spec['title'], claim=spec['claim'], source_sha256=job['source']['sha256'],
        frame_count=len(rows), sources=sources, output=spec['output'], output_sha256=sha256(output))
    if annotated:
        data['public_annotations'] = {'title': spec['title'], 'items': annotations}
    data['edits'] = operations
    data['export'] = {'width': width, 'height': height, 'bytes': output.stat().st_size,
                      'basis': 'local budget, not WeChat acceptance'}
    write_json(manifest, data)
    return output, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', required=True, type=Path); parser.add_argument('--spec', required=True, type=Path)
    parser.add_argument('--font', default=os.environ.get('ARTICLE_FONT')); parser.add_argument('--width', type=int, default=960)
    args = parser.parse_args()
    try:
        if not args.font:
            raise ValueError('provide --font or ARTICLE_FONT; Chinese font is not bundled')
        output, manifest = build(args.job, read_json(args.spec), args.font, args.width)
        print(f'COLLAGE {output}\nMANIFEST {manifest}')
    except (ValueError, KeyError, OSError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr); raise SystemExit(2)


if __name__ == '__main__':
    main()
